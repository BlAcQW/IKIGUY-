import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
	'Access-Control-Allow-Origin': '*',
	'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface ExportRequest {
	reportType: 'usage' | 'performance' | 'conversions';
	timeRange: '7d' | '30d' | '90d' | '1y';
	userId: string;
}

serve(async (req) => {
	// Handle CORS preflight requests
	if (req.method === 'OPTIONS') {
		return new Response('ok', { headers: corsHeaders })
	}

	try {
		const supabaseClient = createClient(
			Deno.env.get('SUPABASE_URL') ?? '',
			Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
		)

		const { reportType, timeRange, userId }: ExportRequest = await req.json()

		if (!userId) {
			throw new Error('User ID is required')
		}

		// Calculate date range
		const now = new Date()
		const daysAgo = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : timeRange === '90d' ? 90 : 365
		const startDate = new Date(now.getTime() - (daysAgo * 24 * 60 * 60 * 1000))

		let csvContent = ''
		let filename = ''

		switch (reportType) {
			case 'usage':
				csvContent = await generateUsageReport(supabaseClient, userId, startDate)
				filename = `usage_analytics_${timeRange}_${new Date().toISOString().split('T')[0]}.csv`
				break

			case 'performance':
				csvContent = await generatePerformanceReport(supabaseClient, userId, startDate)
				filename = `performance_analytics_${timeRange}_${new Date().toISOString().split('T')[0]}.csv`
				break

			case 'conversions':
				csvContent = await generateConversionReport(supabaseClient, userId, startDate)
				filename = `conversion_analytics_${timeRange}_${new Date().toISOString().split('T')[0]}.csv`
				break

			default:
				throw new Error('Invalid report type')
		}

		return new Response(
			JSON.stringify({
				csvContent,
				filename,
				reportType,
				timeRange,
				generatedAt: new Date().toISOString()
			}),
			{
				headers: { ...corsHeaders, 'Content-Type': 'application/json' },
				status: 200,
			}
		)

	} catch (error) {
		console.error('Error in export-analytics:', error)
		return new Response(
			JSON.stringify({ error: error.message }),
			{
				headers: { ...corsHeaders, 'Content-Type': 'application/json' },
				status: 400,
			}
		)
	}
})

async function generateUsageReport(supabase: any, userId: string, startDate: Date): Promise<string> {
	// Fetch demo sessions
	const { data: demoSessions, error: sessionError } = await supabase
		.from('demo_sessions')
		.select('*')
		.gte('started_at', startDate.toISOString())

	if (sessionError) throw sessionError

	// Fetch demo analytics
	const { data: demoAnalytics, error: analyticsError } = await supabase
		.from('demo_analytics')
		.select('*')
		.gte('created_at', startDate.toISOString())

	if (analyticsError) throw analyticsError

	// Generate CSV content
	const headers = ['Date', 'Total Sessions', 'Unique Users', 'Avg Session Duration', 'Total Views', 'Total Interactions']
	const rows = []

	// Group by date
	const sessionsByDate = new Map()
	const analyticsByDate = new Map()

	demoSessions?.forEach(session => {
		const date = new Date(session.created_at).toISOString().split('T')[0]
		if (!sessionsByDate.has(date)) {
			sessionsByDate.set(date, [])
		}
		sessionsByDate.get(date).push(session)
	})

	demoAnalytics?.forEach(analytics => {
		const date = new Date(analytics.created_at).toISOString().split('T')[0]
		if (!analyticsByDate.has(date)) {
			analyticsByDate.set(date, [])
		}
		analyticsByDate.get(date).push(analytics)
	})

	// Generate daily data
	const dates = Array.from(new Set([...sessionsByDate.keys(), ...analyticsByDate.keys()])).sort()

	dates.forEach(date => {
		const sessions = sessionsByDate.get(date) || []
		const analytics = analyticsByDate.get(date) || []

		const totalSessions = sessions.length
		const uniqueUsers = new Set(sessions.map(s => s.user_agent)).size
		const avgSessionDuration = sessions.length > 0
			? sessions.reduce((sum, s) => sum + (s.duration || 0), 0) / sessions.length
			: 0
		const totalViews = analytics.reduce((sum, a) => sum + (a.views || 0), 0)
		const totalInteractions = analytics.reduce((sum, a) => sum + (a.interactions || 0), 0)

		rows.push([
			date,
			totalSessions,
			uniqueUsers,
			avgSessionDuration.toFixed(2),
			totalViews,
			totalInteractions
		])
	})

	return generateCSV(headers, rows)
}

async function generatePerformanceReport(supabase: any, userId: string, startDate: Date): Promise<string> {
	// Fetch demo sessions for performance metrics
	const { data: demoSessions, error: sessionError } = await supabase
		.from('demo_sessions')
		.select('*')
		.gte('started_at', startDate.toISOString())

	if (sessionError) throw sessionError

	// Generate CSV content
	const headers = ['Date', 'Total Sessions', 'Avg Session Duration', 'Error Rate', 'Response Time', 'Uptime']
	const rows = []

	// Group by date
	const sessionsByDate = new Map()
	demoSessions?.forEach(session => {
		const date = new Date(session.started_at).toISOString().split('T')[0]
		if (!sessionsByDate.has(date)) {
			sessionsByDate.set(date, [])
		}
		sessionsByDate.get(date).push(session)
	})

	// Generate daily data
	const dates = Array.from(sessionsByDate.keys()).sort()

	dates.forEach(date => {
		const sessions = sessionsByDate.get(date) || []

		const totalSessions = sessions.length
		const avgSessionDuration = sessions.length > 0
			? sessions.reduce((sum, s) => sum + (s.duration || 0), 0) / sessions.length
			: 0
		const errorRate = 0.8 // Simulated
		const responseTime = 245 // Simulated
		const uptime = 99.9 // Simulated

		rows.push([
			date,
			totalSessions,
			avgSessionDuration.toFixed(2),
			errorRate.toFixed(2),
			responseTime,
			uptime.toFixed(1)
		])
	})

	return generateCSV(headers, rows)
}

async function generateConversionReport(supabase: any, userId: string, startDate: Date): Promise<string> {
	// Fetch demo analytics
	const { data: demoAnalytics, error: analyticsError } = await supabase
		.from('demo_analytics')
		.select('*')
		.gte('created_at', startDate.toISOString())

	if (analyticsError) throw analyticsError

	// Fetch custom demos for demo names
	const { data: demos, error: demosError } = await supabase
		.from('custom_demos')
		.select('id, name')
		.eq('user_id', userId)

	if (demosError) throw demosError

	const demoMap = new Map(demos?.map(d => [d.id, d.name]) || [])

	// Generate CSV content
	const headers = ['Date', 'Demo Name', 'Views', 'Interactions', 'Shares', 'Embeds', 'Conversions', 'Conversion Rate']
	const rows = []

	// Group by date and demo
	const analyticsByDateAndDemo = new Map()

	demoAnalytics?.forEach(analytics => {
		const date = new Date(analytics.created_at).toISOString().split('T')[0]
		const demoId = analytics.demo_id
		const key = `${date}_${demoId}`

		if (!analyticsByDateAndDemo.has(key)) {
			analyticsByDateAndDemo.set(key, {
				date,
				demoId,
				views: 0,
				interactions: 0,
				shares: 0,
				embeds: 0,
				conversions: 0
			})
		}

		const entry = analyticsByDateAndDemo.get(key)
		entry.views += analytics.views || 0
		entry.interactions += analytics.interactions || 0
		entry.shares += analytics.shares || 0
		entry.embeds += analytics.embeds || 0
		entry.conversions += analytics.conversions || 0
	})

	// Generate rows
	analyticsByDateAndDemo.forEach(entry => {
		const conversionRate = entry.views > 0 ? (entry.conversions / entry.views) * 100 : 0
		const demoName = demoMap.get(entry.demoId) || 'Unknown Demo'

		rows.push([
			entry.date,
			demoName,
			entry.views,
			entry.interactions,
			entry.shares,
			entry.embeds,
			entry.conversions,
			conversionRate.toFixed(2)
		])
	})

	// Sort by date
	rows.sort((a, b) => new Date(a[0]).getTime() - new Date(b[0]).getTime())

	return generateCSV(headers, rows)
}

function generateCSV(headers: string[], rows: any[][]): string {
	const csvRows = [headers.join(',')]

	rows.forEach(row => {
		const escapedRow = row.map(cell => {
			if (typeof cell === 'string' && cell.includes(',')) {
				return `"${cell.replace(/"/g, '""')}"`
			}
			return cell
		})
		csvRows.push(escapedRow.join(','))
	})

	return csvRows.join('\n')
}

