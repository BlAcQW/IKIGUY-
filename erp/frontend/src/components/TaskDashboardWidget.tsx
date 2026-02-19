/**
 * TaskDashboardWidget Component
 *
 * Dashboard widget showing assigned tasks with priority sorting
 */

import { useState, useEffect } from 'react'
import { CheckCircle, Clock, AlertTriangle, ArrowRight } from 'lucide-react'
import api from '@/lib/api'

interface TaskDashboardWidgetProps {
  onTaskClick?: (taskId: string) => void
}

export default function TaskDashboardWidget({ onTaskClick }: TaskDashboardWidgetProps) {
  const [tasks, setTasks] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'todo' | 'in_progress' | 'overdue'>('all')

  useEffect(() => {
    fetchTasks()
  }, [filter])

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filter !== 'all' && filter !== 'overdue') {
        params.append('status_filter', filter)
      }

      const response = await api.get(`/crm/tasks/my-tasks?${params}`)
      let tasksData = response.data

      // Filter overdue tasks client-side
      if (filter === 'overdue') {
        const now = new Date()
        tasksData = tasksData.filter((task: any) =>
          task.due_date && new Date(task.due_date) < now && task.status !== 'completed'
        )
      }

      // Sort by priority and due date
      tasksData.sort((a: any, b: any) => {
        const priorityOrder: Record<string, number> = { urgent: 0, high: 1, medium: 2, low: 3 }
        const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority]
        if (priorityDiff !== 0) return priorityDiff

        if (a.due_date && b.due_date) {
          return new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
        }
        return 0
      })

      setTasks(tasksData.slice(0, 10)) // Show top 10 tasks
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-100 text-red-800'
      case 'high':
        return 'bg-orange-100 text-orange-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'low':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'urgent':
      case 'high':
        return <AlertTriangle className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600'
      case 'in_progress':
        return 'text-blue-600'
      case 'todo':
        return 'text-gray-600'
      default:
        return 'text-gray-600'
    }
  }

  const formatDueDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = date.getTime() - now.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays < 0) {
      return `Overdue by ${Math.abs(diffDays)} days`
    } else if (diffDays === 0) {
      return 'Due today'
    } else if (diffDays === 1) {
      return 'Due tomorrow'
    } else if (diffDays <= 7) {
      return `Due in ${diffDays} days`
    } else {
      return date.toLocaleDateString()
    }
  }

  const isOverdue = (dateString: string) => {
    return new Date(dateString) < new Date()
  }

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-center items-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">My Tasks</h2>
          <div className="flex space-x-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 text-xs font-medium rounded-md ${
                filter === 'all'
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('todo')}
              className={`px-3 py-1 text-xs font-medium rounded-md ${
                filter === 'todo'
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              To Do
            </button>
            <button
              onClick={() => setFilter('in_progress')}
              className={`px-3 py-1 text-xs font-medium rounded-md ${
                filter === 'in_progress'
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              In Progress
            </button>
            <button
              onClick={() => setFilter('overdue')}
              className={`px-3 py-1 text-xs font-medium rounded-md ${
                filter === 'overdue'
                  ? 'bg-red-100 text-red-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Overdue
            </button>
          </div>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {tasks.length === 0 ? (
          <div className="px-6 py-8 text-center text-gray-500">
            <CheckCircle className="h-12 w-12 mx-auto mb-2 text-gray-400" />
            <p>No tasks found</p>
            <p className="text-sm">
              {filter === 'overdue'
                ? 'Great! No overdue tasks.'
                : 'All caught up!'}
            </p>
          </div>
        ) : (
          tasks.map((task) => (
            <div
              key={task.id}
              className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => onTaskClick?.(task.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getPriorityColor(task.priority)}`}>
                      {getPriorityIcon(task.priority)}
                      <span className="ml-1 capitalize">{task.priority}</span>
                    </span>
                    <span className={`text-xs font-medium capitalize ${getStatusColor(task.status)}`}>
                      {task.status.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {task.title}
                  </p>
                  {task.description && (
                    <p className="text-sm text-gray-500 truncate mt-1">
                      {task.description}
                    </p>
                  )}
                  {task.due_date && (
                    <p className={`text-xs mt-1 ${
                      isOverdue(task.due_date) && task.status !== 'completed'
                        ? 'text-red-600 font-medium'
                        : 'text-gray-500'
                    }`}>
                      <Clock className="inline h-3 w-3 mr-1" />
                      {formatDueDate(task.due_date)}
                    </p>
                  )}
                  {task.estimated_hours && (
                    <p className="text-xs text-gray-500 mt-1">
                      Est. {task.estimated_hours}h
                      {task.actual_hours && ` • Actual: ${task.actual_hours}h`}
                    </p>
                  )}
                </div>
                <ArrowRight className="h-5 w-5 text-gray-400 flex-shrink-0 ml-4" />
              </div>
            </div>
          ))
        )}
      </div>

      {tasks.length > 0 && (
        <div className="px-6 py-3 bg-gray-50 text-center">
          <button
            onClick={() => window.location.href = '/crm?tab=tasks'}
            className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            View all tasks →
          </button>
        </div>
      )}
    </div>
  )
}
