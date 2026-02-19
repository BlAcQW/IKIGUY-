/**
 * Tasks Page - CRM Task Management
 *
 * Full task list view with create/edit/complete functionality
 */

import { useState, useEffect } from 'react'
import { Plus } from 'lucide-react'
import api from '@/lib/api'
import DataTable, { Column } from '@/components/DataTable'
import FormModal from '@/components/FormModal'
import DeleteConfirmation from '@/components/DeleteConfirmation'

export default function TasksPage() {
  const [tasks, setTasks] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [selectedTask, setSelectedTask] = useState<any>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState<any>({})
  const [filter, setFilter] = useState<'all' | 'todo' | 'in_progress' | 'completed'>('all')

  useEffect(() => {
    fetchTasks()
  }, [filter])

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filter !== 'all') {
        params.append('status_filter', filter)
      }

      const response = await api.get(`/crm/tasks/my-tasks?${params}`)
      setTasks(response.data)
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setSelectedTask(null)
    setFormData({
      title: '',
      description: '',
      priority: 'medium',
      status: 'todo',
      due_date: '',
      estimated_hours: ''
    })
    setIsModalOpen(true)
  }

  const handleEdit = (task: any) => {
    setSelectedTask(task)
    setFormData({
      ...task,
      due_date: task.due_date ? new Date(task.due_date).toISOString().slice(0, 16) : ''
    })
    setIsModalOpen(true)
  }

  const handleDelete = (task: any) => {
    setSelectedTask(task)
    setIsDeleteOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const payload = {
        ...formData,
        due_date: formData.due_date ? new Date(formData.due_date).toISOString() : undefined,
        estimated_hours: formData.estimated_hours ? parseFloat(formData.estimated_hours) : undefined
      }

      if (selectedTask) {
        await api.patch(`/crm/tasks/${selectedTask.id}`, payload)
      } else {
        await api.post('/crm/tasks', payload)
      }
      setIsModalOpen(false)
      fetchTasks()
    } catch (error) {
      console.error('Failed to save task:', error)
      alert('Failed to save task. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Complete task functionality (can be added to table actions later)
  // const handleComplete = async (taskId: string, actualHours?: number) => {
  //   try {
  //     const params = actualHours ? `?actual_hours=${actualHours}` : ''
  //     await api.patch(`/crm/tasks/${taskId}/complete${params}`)
  //     fetchTasks()
  //   } catch (error) {
  //     console.error('Failed to complete task:', error)
  //     alert('Failed to complete task. Please try again.')
  //   }
  // }

  const handleConfirmDelete = async () => {
    if (!selectedTask) return

    setIsSubmitting(true)
    try {
      await api.delete(`/crm/tasks/${selectedTask.id}`)
      setIsDeleteOpen(false)
      fetchTasks()
    } catch (error) {
      console.error('Failed to delete task:', error)
      alert('Failed to delete task. Please try again.')
    } finally {
      setIsSubmitting(false)
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'in_progress':
        return 'bg-blue-100 text-blue-800'
      case 'todo':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const isOverdue = (dateString: string, status: string) => {
    if (status === 'completed') return false
    return new Date(dateString) < new Date()
  }

  const columns: Column<any>[] = [
    {
      key: 'title',
      label: 'Task',
      render: (task) => (
        <div>
          <div className="font-medium text-gray-900">{task.title}</div>
          {task.description && (
            <div className="text-sm text-gray-500 mt-1">{task.description}</div>
          )}
        </div>
      )
    },
    {
      key: 'priority',
      label: 'Priority',
      render: (task) => (
        <span className={`px-2 py-1 text-xs rounded-full font-medium capitalize ${getPriorityColor(task.priority)}`}>
          {task.priority}
        </span>
      )
    },
    {
      key: 'status',
      label: 'Status',
      render: (task) => (
        <span className={`px-2 py-1 text-xs rounded-full font-medium capitalize ${getStatusColor(task.status)}`}>
          {task.status.replace('_', ' ')}
        </span>
      )
    },
    {
      key: 'due_date',
      label: 'Due Date',
      render: (task) => task.due_date ? (
        <div className={`text-sm ${
          isOverdue(task.due_date, task.status) ? 'text-red-600 font-medium' : 'text-gray-700'
        }`}>
          {new Date(task.due_date).toLocaleDateString()}
          {isOverdue(task.due_date, task.status) && (
            <div className="text-xs text-red-600">Overdue</div>
          )}
        </div>
      ) : (
        <span className="text-gray-400">-</span>
      )
    },
    {
      key: 'estimated_hours',
      label: 'Hours',
      render: (task) => (
        <div className="text-sm text-gray-700">
          {task.estimated_hours ? `${task.estimated_hours}h` : '-'}
          {task.actual_hours && (
            <div className="text-xs text-gray-500">Actual: {task.actual_hours}h</div>
          )}
        </div>
      )
    }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="sm:flex sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Tasks</h1>
              <p className="mt-2 text-sm text-gray-700">
                Manage and track your CRM tasks
              </p>
            </div>
            <div className="mt-4 sm:mt-0">
              <button
                onClick={handleCreate}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <Plus className="h-5 w-5 mr-2" />
                New Task
              </button>
            </div>
          </div>

          {/* Filters */}
          <div className="mt-4 flex space-x-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 text-sm font-medium rounded-md ${
                filter === 'all'
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              All Tasks
            </button>
            <button
              onClick={() => setFilter('todo')}
              className={`px-4 py-2 text-sm font-medium rounded-md ${
                filter === 'todo'
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              To Do
            </button>
            <button
              onClick={() => setFilter('in_progress')}
              className={`px-4 py-2 text-sm font-medium rounded-md ${
                filter === 'in_progress'
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              In Progress
            </button>
            <button
              onClick={() => setFilter('completed')}
              className={`px-4 py-2 text-sm font-medium rounded-md ${
                filter === 'completed'
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              Completed
            </button>
          </div>
        </div>

        {/* Table */}
        <DataTable
          columns={columns}
          data={tasks}
          loading={loading}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </div>

      {/* Create/Edit Modal */}
      <FormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={selectedTask ? 'Edit Task' : 'Create Task'}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title *
            </label>
            <input
              type="text"
              required
              value={formData.title || ''}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                value={formData.priority || 'medium'}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={formData.status || 'todo'}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              >
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Due Date
              </label>
              <input
                type="datetime-local"
                value={formData.due_date || ''}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Estimated Hours
              </label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={formData.estimated_hours || ''}
                onChange={(e) => setFormData({ ...formData, estimated_hours: e.target.value })}
                className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>
      </FormModal>

      {/* Delete Confirmation */}
      <DeleteConfirmation
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        onConfirm={handleConfirmDelete}
        title="Delete Task"
        message="Are you sure you want to delete this task? This action cannot be undone."
      />
    </div>
  )
}
