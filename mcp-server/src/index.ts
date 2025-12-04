#!/usr/bin/env node
/**
 * WASTE Master Brain MCP Server
 *
 * Connects Claude Code to waste intelligence data including:
 * - Rate database with benchmarks and trends
 * - Semantic email search
 * - Property KPI tracking
 * - Extraction persistence
 *
 * Usage:
 *   npm run dev   # Development mode
 *   npm start     # Production mode
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import initSqlJs, { Database as SqlJsDatabase } from "sql.js";
import { spawn } from "child_process";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

// Get directory paths
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, "../..");

// Database path
const DB_PATH =
  process.env.DB_PATH || path.join(PROJECT_ROOT, "data", "wastewise.db");
const GOOGLE_API_KEY = process.env.GOOGLE_API_KEY;

// Initialize database
let db: SqlJsDatabase;

async function initDatabase(): Promise<void> {
  const SQL = await initSqlJs();
  try {
    if (fs.existsSync(DB_PATH)) {
      const fileBuffer = fs.readFileSync(DB_PATH);
      db = new SQL.Database(fileBuffer);
    } else {
      db = new SQL.Database();
      console.error(`Database not found at ${DB_PATH}, created new empty database`);
    }
  } catch (error) {
    console.error(`Failed to open database at ${DB_PATH}:`, error);
    process.exit(1);
  }
}

// Helper to save database after writes
function saveDatabase(): void {
  const data = db.export();
  const buffer = Buffer.from(data);
  fs.writeFileSync(DB_PATH, buffer);
}

// Helper to run SQL and get results
function dbAll(sql: string, params: (string | number)[] = []): Record<string, unknown>[] {
  const stmt = db.prepare(sql);
  stmt.bind(params);
  const results: Record<string, unknown>[] = [];
  while (stmt.step()) {
    results.push(stmt.getAsObject() as Record<string, unknown>);
  }
  stmt.free();
  return results;
}

function dbGet(sql: string, params: (string | number)[] = []): Record<string, unknown> | undefined {
  const results = dbAll(sql, params);
  return results[0];
}

function dbRun(sql: string, params: (string | number | null)[] = []): number {
  db.run(sql, params);
  saveDatabase();
  // Get last insert rowid
  const result = dbGet("SELECT last_insert_rowid() as id");
  return (result?.id as number) || 0;
}

// Tool schemas using Zod
const QueryRatesSchema = z.object({
  vendor: z.string().optional().describe("Filter by hauler name (e.g., 'WM', 'Republic')"),
  service_type: z
    .enum(["compactor", "dumpster", "recycling", "organics", "bulky"])
    .optional()
    .describe("Type of waste service"),
  rate_type: z
    .enum([
      "haul_fee",
      "disposal_per_ton",
      "rental",
      "fuel_surcharge",
      "environmental_fee",
      "admin_fee",
      "contamination_fee",
    ])
    .optional()
    .describe("Type of rate/fee"),
  region: z.string().optional().describe("Geographic region for filtering"),
});

const SearchEmailsSchema = z.object({
  query: z.string().describe("Natural language search query"),
  max_results: z.number().optional().default(5).describe("Maximum results to return"),
});

const GetPropertyKPIsSchema = z.object({
  property_name: z.string().describe("Name of the property"),
  period: z.string().optional().describe("Period in YYYY-MM format"),
  include_history: z.boolean().optional().default(false).describe("Include historical KPIs"),
});

const SaveExtractionSchema = z.object({
  property_name: z.string().describe("Property name"),
  extraction_type: z.enum(["invoice", "contract", "kpi"]).describe("Type of extraction"),
  vendor: z.string().optional().describe("Vendor name"),
  data: z.record(z.any()).describe("Extracted data as JSON object"),
  source_document: z.string().optional().describe("Source file reference"),
});

const GenerateKPIChartSchema = z.object({
  chart_type: z.enum(["bar", "line", "pie", "area"]).describe("Chart visualization type"),
  kpi_type: z
    .enum(["cost_per_door", "yards_per_door", "contamination", "pricing_trends"])
    .describe("KPI metric to visualize"),
  title: z.string().describe("Chart title"),
  description: z.string().optional().describe("Chart description"),
  property_filter: z.string().optional().describe("Filter by property name"),
  vendor_filter: z.string().optional().describe("Filter by vendor"),
  months: z.number().optional().default(12).describe("Number of months for trends"),
});

// Tool definitions for MCP
const TOOLS = [
  {
    name: "query_rates",
    description:
      "Search historical waste hauler rates by vendor, service type, and region. Returns benchmarks including average, min, max rates and sample counts.",
    inputSchema: {
      type: "object" as const,
      properties: {
        vendor: { type: "string", description: "Filter by hauler name (e.g., 'WM', 'Republic')" },
        service_type: {
          type: "string",
          enum: ["compactor", "dumpster", "recycling", "organics", "bulky"],
          description: "Type of waste service",
        },
        rate_type: {
          type: "string",
          enum: [
            "haul_fee",
            "disposal_per_ton",
            "rental",
            "fuel_surcharge",
            "environmental_fee",
            "admin_fee",
            "contamination_fee",
          ],
          description: "Type of rate/fee",
        },
        region: { type: "string", description: "Geographic region" },
      },
    },
  },
  {
    name: "search_emails",
    description:
      "Semantic search over waste management email knowledge base using Gemini embeddings. Find relevant past discussions, negotiations, and issue resolutions.",
    inputSchema: {
      type: "object" as const,
      properties: {
        query: { type: "string", description: "Natural language search query" },
        max_results: { type: "number", description: "Maximum results (default: 5)" },
      },
      required: ["query"],
    },
  },
  {
    name: "get_property_kpis",
    description:
      "Get KPI metrics for a property including cost per door, yards per door, contamination rate, and fee burden percentage.",
    inputSchema: {
      type: "object" as const,
      properties: {
        property_name: { type: "string", description: "Name of the property" },
        period: { type: "string", description: "Period in YYYY-MM format" },
        include_history: { type: "boolean", description: "Include historical KPIs" },
      },
      required: ["property_name"],
    },
  },
  {
    name: "save_extraction",
    description:
      "Save WasteWise extraction results (invoices, contracts, KPIs) to the Master Brain database for future analysis and benchmarking.",
    inputSchema: {
      type: "object" as const,
      properties: {
        property_name: { type: "string", description: "Property name" },
        extraction_type: {
          type: "string",
          enum: ["invoice", "contract", "kpi"],
          description: "Type of extraction",
        },
        vendor: { type: "string", description: "Vendor name" },
        data: { type: "object", description: "Extracted data" },
        source_document: { type: "string", description: "Source file reference" },
      },
      required: ["property_name", "extraction_type", "data"],
    },
  },
  {
    name: "generate_kpi_chart",
    description:
      "Generate structured chart data for waste management KPI visualizations. Returns data formatted for Recharts rendering.",
    inputSchema: {
      type: "object" as const,
      properties: {
        chart_type: {
          type: "string",
          enum: ["bar", "line", "pie", "area"],
          description: "Chart type",
        },
        kpi_type: {
          type: "string",
          enum: ["cost_per_door", "yards_per_door", "contamination", "pricing_trends"],
          description: "KPI to visualize",
        },
        title: { type: "string", description: "Chart title" },
        description: { type: "string", description: "Chart description" },
        property_filter: { type: "string", description: "Filter by property" },
        vendor_filter: { type: "string", description: "Filter by vendor" },
        months: { type: "number", description: "Months for trends (default: 12)" },
      },
      required: ["chart_type", "kpi_type", "title"],
    },
  },
];

// Tool handlers
async function handleQueryRates(args: z.infer<typeof QueryRatesSchema>) {
  const conditions: string[] = [];
  const params: (string | number)[] = [];

  if (args.vendor) {
    conditions.push("vendor = ?");
    params.push(args.vendor);
  }
  if (args.service_type) {
    conditions.push("service_type = ?");
    params.push(args.service_type);
  }
  if (args.rate_type) {
    conditions.push("rate_type = ?");
    params.push(args.rate_type);
  }
  if (args.region) {
    conditions.push("region = ?");
    params.push(args.region);
  }

  const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

  const stats = dbGet(
    `SELECT
      AVG(rate_value) as avg_rate,
      MIN(rate_value) as min_rate,
      MAX(rate_value) as max_rate,
      COUNT(*) as sample_count
    FROM rate_history
    ${whereClause}`,
    params
  ) as { avg_rate: number; min_rate: number; max_rate: number; sample_count: number } | undefined;

  // Get recent trends
  const trends = dbAll(
    `SELECT
      strftime('%Y-%m', effective_date) as period,
      AVG(rate_value) as avg_rate
    FROM rate_history
    ${whereClause}
    GROUP BY period
    ORDER BY period DESC
    LIMIT 6`,
    params
  );

  const avgRate = stats?.avg_rate;
  const minRate = stats?.min_rate;
  const maxRate = stats?.max_rate;
  const sampleCount = stats?.sample_count || 0;

  return {
    benchmarks: {
      avg_rate: avgRate ? Math.round(avgRate * 100) / 100 : null,
      min_rate: minRate,
      max_rate: maxRate,
      sample_count: sampleCount,
    },
    filters: args,
    recent_trends: trends,
    interpretation:
      sampleCount > 0
        ? `Based on ${sampleCount} rate records, average is $${avgRate?.toFixed(2)} (range: $${minRate} - $${maxRate})`
        : "No rate data found for these filters.",
  };
}

async function handleSearchEmails(args: z.infer<typeof SearchEmailsSchema>): Promise<object> {
  // Call Python semantic_rag.py for search
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(PROJECT_ROOT, "scripts", "semantic_rag.py");
    const pythonProcess = spawn("python", [
      scriptPath,
      "--query",
      args.query,
      "--max-results",
      String(args.max_results || 5),
    ], {
      env: { ...process.env, GOOGLE_API_KEY: GOOGLE_API_KEY || "" },
    });

    let output = "";
    let errorOutput = "";

    pythonProcess.stdout.on("data", (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on("data", (data) => {
      errorOutput += data.toString();
    });

    pythonProcess.on("close", (code) => {
      if (code !== 0) {
        resolve({
          query: args.query,
          error: `Search failed: ${errorOutput}`,
          results: [],
        });
      } else {
        // Parse the answer from output
        const answerMatch = output.match(/Answer:\n={80}\n([\s\S]+)/);
        resolve({
          query: args.query,
          answer: answerMatch ? answerMatch[1].trim() : output,
          results_found: true,
        });
      }
    });
  });
}

async function handleGetPropertyKPIs(args: z.infer<typeof GetPropertyKPIsSchema>) {
  // Get property
  const property = dbGet(
    "SELECT * FROM properties WHERE name = ?",
    [args.property_name]
  ) as { id: number; name: string; unit_count: number } | undefined;

  if (!property) {
    return {
      property_name: args.property_name,
      error: "Property not found",
      suggestion: "Use save_extraction to add this property first",
    };
  }

  // Get KPIs
  let kpis;
  if (args.include_history) {
    kpis = dbAll(
      `SELECT * FROM kpi_history
      WHERE property_id = ?
      ORDER BY period DESC
      LIMIT 12`,
      [property.id]
    );
  } else if (args.period) {
    kpis = dbGet(
      `SELECT * FROM kpi_history
      WHERE property_id = ? AND period = ?`,
      [property.id, args.period]
    );
  } else {
    kpis = dbGet(
      `SELECT * FROM kpi_history
      WHERE property_id = ?
      ORDER BY period DESC
      LIMIT 1`,
      [property.id]
    );
  }

  return {
    property: {
      name: property.name,
      unit_count: property.unit_count,
    },
    kpis: kpis || [],
    period: args.period || "latest",
  };
}

async function handleSaveExtraction(args: z.infer<typeof SaveExtractionSchema>) {
  // Get or create property
  let property = dbGet(
    "SELECT id FROM properties WHERE name = ?",
    [args.property_name]
  ) as { id: number } | undefined;

  if (!property) {
    const id = dbRun(
      "INSERT INTO properties (name) VALUES (?)",
      [args.property_name]
    );
    property = { id };
  }

  let savedId: number;

  switch (args.extraction_type) {
    case "invoice": {
      const data = args.data;
      savedId = dbRun(
        `INSERT INTO invoices
        (property_id, vendor, invoice_number, invoice_date, total_amount, haul_count, tons_total,
         base_service_cost, disposal_cost, fees_total, source_file, extraction_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [
          property.id,
          (args.vendor || data.vendor) as string,
          data.invoice_number as string | null,
          data.invoice_date as string | null,
          data.total_amount as number | null,
          data.haul_count as number | null,
          data.tons_total as number | null,
          data.base_service_cost as number | null,
          data.disposal_cost as number | null,
          data.fees_total as number | null,
          args.source_document || null,
          JSON.stringify(data)
        ]
      );

      // Also save rates if present
      if (data.rates && Array.isArray(data.rates)) {
        for (const rate of data.rates as Array<{service_type: string; rate_type: string; rate_value: number}>) {
          dbRun(
            `INSERT INTO rate_history
            (property_id, vendor, service_type, rate_type, rate_value, effective_date, source_document)
            VALUES (?, ?, ?, ?, ?, ?, ?)`,
            [
              property.id,
              (args.vendor || data.vendor) as string,
              rate.service_type,
              rate.rate_type,
              rate.rate_value,
              data.invoice_date as string,
              args.source_document || null
            ]
          );
        }
      }
      break;
    }
    case "kpi": {
      const data = args.data;
      savedId = dbRun(
        `INSERT INTO kpi_history
        (property_id, period, cost_per_door, yards_per_door, contamination_rate, fee_burden_pct, total_cost, source_invoice_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(property_id, period) DO UPDATE SET
          cost_per_door = excluded.cost_per_door,
          yards_per_door = excluded.yards_per_door,
          contamination_rate = excluded.contamination_rate,
          fee_burden_pct = excluded.fee_burden_pct,
          total_cost = excluded.total_cost`,
        [
          property.id,
          data.period as string,
          data.cost_per_door as number | null,
          data.yards_per_door as number | null,
          data.contamination_rate as number | null,
          data.fee_burden_pct as number | null,
          data.total_cost as number | null,
          args.source_document || null
        ]
      );
      break;
    }
    case "contract": {
      const data = args.data;
      savedId = dbRun(
        `INSERT INTO contracts
        (property_id, vendor, contract_type, start_date, end_date, auto_renewal,
         renewal_notice_days, termination_notice_days, rate_increase_cap, key_terms, source_file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [
          property.id,
          args.vendor || null,
          data.contract_type as string | null,
          data.start_date as string | null,
          data.end_date as string | null,
          data.auto_renewal ? 1 : 0,
          data.renewal_notice_days as number | null,
          data.termination_notice_days as number | null,
          data.rate_increase_cap as number | null,
          JSON.stringify(data.key_terms),
          args.source_document || null
        ]
      );
      break;
    }
    default:
      throw new Error(`Unknown extraction type: ${args.extraction_type}`);
  }

  return {
    success: true,
    extraction_type: args.extraction_type,
    property_name: args.property_name,
    saved_id: savedId,
    message: `Successfully saved ${args.extraction_type} data for ${args.property_name}`,
  };
}

async function handleGenerateKPIChart(args: z.infer<typeof GenerateKPIChartSchema>) {
  let data: unknown[];
  let chartConfig: Record<string, { label: string; color: string }>;

  switch (args.kpi_type) {
    case "cost_per_door": {
      const rows = dbAll(
        `SELECT p.name, k.period, k.cost_per_door as value
        FROM kpi_history k
        JOIN properties p ON k.property_id = p.id
        ${args.property_filter ? "WHERE p.name LIKE ?" : ""}
        ORDER BY k.period DESC
        LIMIT ?`,
        args.property_filter ? [`%${args.property_filter}%`, args.months] : [args.months]
      );
      data = rows;
      chartConfig = {
        value: { label: "Cost/Door ($)", color: "hsl(var(--chart-1))" },
      };
      break;
    }
    case "yards_per_door": {
      const rows = dbAll(
        `SELECT p.name, k.period, k.yards_per_door as value
        FROM kpi_history k
        JOIN properties p ON k.property_id = p.id
        ORDER BY k.period DESC
        LIMIT ?`,
        [args.months]
      );
      data = rows;
      chartConfig = {
        value: { label: "Yards/Door", color: "hsl(var(--chart-2))" },
      };
      break;
    }
    case "pricing_trends": {
      const rows = dbAll(
        `SELECT
          strftime('%Y-%m', effective_date) as period,
          vendor,
          AVG(rate_value) as value
        FROM rate_history
        ${args.vendor_filter ? "WHERE vendor = ?" : ""}
        GROUP BY period, vendor
        ORDER BY period DESC
        LIMIT ?`,
        args.vendor_filter ? [args.vendor_filter, args.months] : [args.months]
      );
      data = rows;
      chartConfig = {
        value: { label: "Avg Rate ($)", color: "hsl(var(--chart-3))" },
      };
      break;
    }
    default:
      data = [];
      chartConfig = {};
  }

  return {
    chartType: args.chart_type,
    kpiType: args.kpi_type,
    config: {
      title: args.title,
      description: args.description || `${args.kpi_type} visualization`,
    },
    data,
    chartConfig,
  };
}

// Create and configure server
const server = new Server(
  {
    name: "waste-master-brain",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// List tools handler
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS,
}));

// Call tool handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result: object;

    switch (name) {
      case "query_rates":
        result = await handleQueryRates(QueryRatesSchema.parse(args));
        break;
      case "search_emails":
        result = await handleSearchEmails(SearchEmailsSchema.parse(args));
        break;
      case "get_property_kpis":
        result = await handleGetPropertyKPIs(GetPropertyKPIsSchema.parse(args));
        break;
      case "save_extraction":
        result = await handleSaveExtraction(SaveExtractionSchema.parse(args));
        break;
      case "generate_kpi_chart":
        result = await handleGenerateKPIChart(GenerateKPIChartSchema.parse(args));
        break;
      default:
        throw new Error(`Unknown tool: ${name}`);
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ error: errorMessage }),
        },
      ],
      isError: true,
    };
  }
});

// List resources handler (database stats)
server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [
    {
      uri: "wastewise://stats",
      name: "Database Statistics",
      description: "Current counts of properties, rates, KPIs, and other data",
      mimeType: "application/json",
    },
  ],
}));

// Read resource handler
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  if (request.params.uri === "wastewise://stats") {
    const stats = {
      properties: (dbGet("SELECT COUNT(*) as count FROM properties") as { count: number })?.count || 0,
      rate_history: (dbGet("SELECT COUNT(*) as count FROM rate_history") as { count: number })?.count || 0,
      kpi_history: (dbGet("SELECT COUNT(*) as count FROM kpi_history") as { count: number })?.count || 0,
      invoices: (dbGet("SELECT COUNT(*) as count FROM invoices") as { count: number })?.count || 0,
      contracts: (dbGet("SELECT COUNT(*) as count FROM contracts") as { count: number })?.count || 0,
      hauler_profiles: (dbGet("SELECT COUNT(*) as count FROM hauler_profiles") as { count: number })?.count || 0,
    };

    return {
      contents: [
        {
          uri: "wastewise://stats",
          mimeType: "application/json",
          text: JSON.stringify(stats, null, 2),
        },
      ],
    };
  }

  throw new Error(`Unknown resource: ${request.params.uri}`);
});

// Start server
async function main() {
  await initDatabase();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("WASTE Master Brain MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
