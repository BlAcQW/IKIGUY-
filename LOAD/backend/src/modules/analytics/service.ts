import { prisma } from '../../database/client.js';
import { Prisma } from '@prisma/client';
import type { CallAnalyticsQuery, SummaryQuery } from './schemas.js';

export interface TimeSeriesPoint {
  period: string;
  total: number;
  completed: number;
  failed: number;
  avgDuration: number;
}

export interface AnalyticsSummary {
  totalCalls: number;
  completedCalls: number;
  failedCalls: number;
  successRate: number;
  avgDuration: number;
  totalMinutes: number;
  byType: { type: string; count: number }[];
  byAssistant: { assistantId: string; assistantName: string; count: number }[];
}

function buildDateRange(from?: string, to?: string): { fromDate: Date; toDate: Date } {
  const toDate = to ? new Date(to) : new Date();
  const fromDate = from ? new Date(from) : new Date(toDate.getTime() - 7 * 24 * 60 * 60 * 1000);
  return { fromDate, toDate };
}

export async function getCallTimeSeries(
  organizationId: string,
  query: CallAnalyticsQuery,
): Promise<TimeSeriesPoint[]> {
  const { fromDate, toDate } = buildDateRange(query.from, query.to);
  const groupBy = query.groupBy ?? 'day';

  const conditions: string[] = [
    `c."organizationId" = '${organizationId}'`,
    `c."createdAt" >= '${fromDate.toISOString()}'`,
    `c."createdAt" <= '${toDate.toISOString()}'`,
  ];

  if (query.assistantId) {
    conditions.push(`c."assistantId" = '${query.assistantId}'`);
  }
  if (query.type) {
    conditions.push(`c."type" = '${query.type}'::"CallType"`);
  }

  const whereClause = conditions.join(' AND ');

  const result = await prisma.$queryRaw<
    { period: Date; total: bigint; completed: bigint; failed: bigint; avg_duration: number | null }[]
  >(
    Prisma.sql`
      SELECT
        date_trunc(${groupBy}, c."createdAt") AS period,
        COUNT(*)::bigint AS total,
        COUNT(*) FILTER (WHERE c."status" = 'ENDED')::bigint AS completed,
        COUNT(*) FILTER (WHERE c."status" = 'FAILED')::bigint AS failed,
        COALESCE(AVG(c."duration") FILTER (WHERE c."duration" IS NOT NULL), 0) AS avg_duration
      FROM "Call" c
      WHERE ${Prisma.raw(whereClause)}
      GROUP BY date_trunc(${groupBy}, c."createdAt")
      ORDER BY period ASC
    `,
  );

  return result.map((row) => ({
    period: row.period.toISOString(),
    total: Number(row.total),
    completed: Number(row.completed),
    failed: Number(row.failed),
    avgDuration: Math.round(Number(row.avg_duration ?? 0)),
  }));
}

export async function getAnalyticsSummary(
  organizationId: string,
  query: SummaryQuery,
): Promise<AnalyticsSummary> {
  const { fromDate, toDate } = buildDateRange(query.from, query.to);

  const where: Prisma.CallWhereInput = {
    organizationId,
    createdAt: { gte: fromDate, lte: toDate },
    ...(query.assistantId ? { assistantId: query.assistantId } : {}),
    ...(query.type ? { type: query.type } : {}),
  };

  const [totalCalls, completedCalls, failedCalls, durationAgg, byTypeResult, byAssistantResult] =
    await Promise.all([
      prisma.call.count({ where }),
      prisma.call.count({ where: { ...where, status: 'ENDED' } }),
      prisma.call.count({ where: { ...where, status: 'FAILED' } }),
      prisma.call.aggregate({
        where: { ...where, duration: { not: null } },
        _avg: { duration: true },
        _sum: { duration: true },
      }),
      prisma.call.groupBy({
        by: ['type'],
        where,
        _count: true,
      }),
      prisma.call.groupBy({
        by: ['assistantId'],
        where,
        _count: true,
        orderBy: { _count: { assistantId: 'desc' } },
        take: 10,
      }),
    ]);

  // Resolve assistant names
  const assistantIds = byAssistantResult.map((r) => r.assistantId);
  const assistants = assistantIds.length > 0
    ? await prisma.assistant.findMany({
        where: { id: { in: assistantIds } },
        select: { id: true, name: true },
      })
    : [];
  const assistantNameMap = new Map(assistants.map((a) => [a.id, a.name]));

  const avgDuration = Math.round(durationAgg._avg.duration ?? 0);
  const totalMinutes = Math.round((durationAgg._sum.duration ?? 0) / 60);
  const successRate = totalCalls > 0 ? Math.round((completedCalls / totalCalls) * 100) : 0;

  return {
    totalCalls,
    completedCalls,
    failedCalls,
    successRate,
    avgDuration,
    totalMinutes,
    byType: byTypeResult.map((r) => ({ type: r.type, count: r._count })),
    byAssistant: byAssistantResult.map((r) => ({
      assistantId: r.assistantId,
      assistantName: assistantNameMap.get(r.assistantId) ?? 'Unknown',
      count: r._count,
    })),
  };
}
