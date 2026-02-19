import { useEffect, useState } from 'react'
import { useOrganization } from '@/contexts/OrganizationContext'
import { Users, DollarSign, FolderKanban, TrendingUp, Loader2, RotateCcw } from 'lucide-react'
import api from '@/services/api'

interface DashboardStats {
  totalCustomers: number
  totalRevenue: number
  activeProjects: number
  totalEmployees: number
  pendingInvoices: number
  revenueGrowth: number
  totalRecurringExpenses: number
  recurringExpensesCount: number
}

export default function Dashboard() {
  const { currentOrganization } = useOrganization()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [currentOrganization])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)

      // Fetch all data in parallel (using max allowed limit of 1000)
      const [customersRes, invoicesRes, projectsRes, employeesRes, recurringExpensesRes] = await Promise.all([
        api.get('/crm/customers', { params: { skip: 0, limit: 1000 } }),
        api.get('/finance/invoices', { params: { skip: 0, limit: 1000 } }),
        api.get('/projects', { params: { skip: 0, limit: 1000 } }),
        api.get('/hr/employees', { params: { skip: 0, limit: 1000 } }),
        api.get('/finance/recurring-expenses', { params: { skip: 0, limit: 1000, active_only: true } }).catch(() => ({ data: { items: [], total: 0 } }))
      ])

      const customers = customersRes.data
      const invoices = invoicesRes.data
      const projects = projectsRes.data
      const employees = employeesRes.data
      const recurringExpenses = recurringExpensesRes.data

      // Calculate active projects (status: active or planning)
      const activeProjects = projects.filter((p: any) =>
        p.status === 'active' || p.status === 'planning'
      ).length

      // Calculate total revenue from paid invoices
      const totalRevenue = invoices
        .filter((inv: any) => inv.status === 'paid')
        .reduce((sum: number, inv: any) => sum + (inv.total_amount || 0), 0)

      // Calculate pending invoices
      const pendingInvoices = invoices.filter((inv: any) =>
        inv.status === 'pending' || inv.status === 'sent'
      ).length

      // Calculate revenue growth (compare last 30 days vs previous 30 days)
      const now = new Date()
      const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      const sixtyDaysAgo = new Date(now.getTime() - 60 * 24 * 60 * 60 * 1000)

      const recentRevenue = invoices
        .filter((inv: any) => {
          if (inv.status !== 'paid' || !inv.paid_date) return false
          const paidDate = new Date(inv.paid_date)
          return paidDate >= thirtyDaysAgo && paidDate <= now
        })
        .reduce((sum: number, inv: any) => sum + (inv.total_amount || 0), 0)

      const previousRevenue = invoices
        .filter((inv: any) => {
          if (inv.status !== 'paid' || !inv.paid_date) return false
          const paidDate = new Date(inv.paid_date)
          return paidDate >= sixtyDaysAgo && paidDate < thirtyDaysAgo
        })
        .reduce((sum: number, inv: any) => sum + (inv.total_amount || 0), 0)

      const revenueGrowth = previousRevenue > 0
        ? ((recentRevenue - previousRevenue) / previousRevenue) * 100
        : 0

      // Calculate total recurring expenses (monthly amounts)
      const recurringExpenseItems = recurringExpenses.items || recurringExpenses || []
      const totalRecurringExpenses = recurringExpenseItems.reduce(
        (sum: number, exp: any) => sum + (exp.amount || 0),
        0
      )

      setStats({
        totalCustomers: customers.length,
        totalRevenue,
        activeProjects,
        totalEmployees: employees.length,
        pendingInvoices,
        revenueGrowth,
        totalRecurringExpenses,
        recurringExpensesCount: recurringExpenseItems.length
      })
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-GH', {
      style: 'currency',
      currency: 'GHS',
      minimumFractionDigits: 2
    }).format(amount)
  }

  const formatPercentage = (value: number) => {
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(1)}%`
  }

  const dashboardStats = stats ? [
    {
      name: 'Total Customers',
      value: stats.totalCustomers.toString(),
      icon: Users,
      change: `${stats.totalCustomers} active`,
      changeType: 'positive'
    },
    {
      name: 'Total Revenue',
      value: formatCurrency(stats.totalRevenue),
      icon: DollarSign,
      change: formatPercentage(stats.revenueGrowth) + ' from last month',
      changeType: stats.revenueGrowth >= 0 ? 'positive' : 'negative'
    },
    {
      name: 'Active Projects',
      value: stats.activeProjects.toString(),
      icon: FolderKanban,
      change: `${stats.activeProjects} in progress`,
      changeType: 'positive'
    },
    {
      name: 'Recurring Expenses',
      value: formatCurrency(stats.totalRecurringExpenses),
      icon: RotateCcw,
      change: `${stats.recurringExpensesCount} active subscriptions`,
      changeType: 'neutral'
    },
    {
      name: 'Total Employees',
      value: stats.totalEmployees.toString(),
      icon: TrendingUp,
      change: `${stats.pendingInvoices} pending invoices`,
      changeType: 'positive'
    },
  ] : []

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
      <p className="text-gray-600 mb-8">
        Welcome to {currentOrganization?.display_name || 'KasaAI ERP'}
      </p>

      {/* Stats Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 mb-8">
          {dashboardStats.map((stat) => (
            <div key={stat.name} className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
                  <p className={`text-sm mt-1 ${
                    stat.changeType === 'positive' ? 'text-green-600' :
                    stat.changeType === 'negative' ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {stat.change}
                  </p>
                </div>
                <stat.icon className="w-12 h-12 text-blue-500" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left">
            <p className="font-medium">Add Customer</p>
            <p className="text-sm text-gray-500 mt-1">Create new customer record</p>
          </button>
          <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left">
            <p className="font-medium">New Invoice</p>
            <p className="text-sm text-gray-500 mt-1">Generate invoice</p>
          </button>
          <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left">
            <p className="font-medium">Add Employee</p>
            <p className="text-sm text-gray-500 mt-1">Onboard new employee</p>
          </button>
          <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left">
            <p className="font-medium">New Project</p>
            <p className="text-sm text-gray-500 mt-1">Start new project</p>
          </button>
        </div>
      </div>
    </div>
  )
}
