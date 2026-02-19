/**
 * Material Library Page
 *
 * Displays all study materials with search and filter functionality.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { materialsApi } from '../lib/api';

interface Material {
  id: string;
  title: string;
  subject: string;
  grade?: number;
  topics: string[];
  file_name: string;
  file_type: string;
  file_size: number;
  chunks_count?: number;
  status: string;
  description?: string;
  created_at: string;
  processed_at?: string;
}

export default function MaterialLibrary() {
  const navigate = useNavigate();
  const [materials, setMaterials] = useState<Material[]>([]);
  const [filteredMaterials, setFilteredMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedGrade, setSelectedGrade] = useState('');

  // Load materials
  useEffect(() => {
    loadMaterials();
  }, []);

  // Apply filters
  useEffect(() => {
    filterMaterials();
  }, [searchQuery, selectedSubject, selectedGrade, materials]);

  const loadMaterials = async () => {
    try {
      setLoading(true);
      const response = await materialsApi.list();
      // Backend returns array directly, not wrapped in {materials: []}
      const materialsArray = Array.isArray(response) ? response : [];
      setMaterials(materialsArray);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load materials');
    } finally {
      setLoading(false);
    }
  };

  const filterMaterials = () => {
    let filtered = [...materials];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (material) =>
          material.title.toLowerCase().includes(query) ||
          material.subject.toLowerCase().includes(query) ||
          material.topics.some((topic) => topic.toLowerCase().includes(query))
      );
    }

    // Subject filter
    if (selectedSubject) {
      filtered = filtered.filter((material) => material.subject === selectedSubject);
    }

    // Grade filter
    if (selectedGrade) {
      filtered = filtered.filter(
        (material) => material.grade === parseInt(selectedGrade)
      );
    }

    setFilteredMaterials(filtered);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this material?')) {
      return;
    }

    try {
      await materialsApi.delete(id);
      // Remove from list immediately (optimistic update)
      setMaterials((prev) => prev.filter((m) => m.id !== id));
      // Show success message
      alert('Material deleted successfully!');
    } catch (err) {
      console.error('Delete error:', err);
      alert(err instanceof Error ? err.message : 'Failed to delete material');
      // Reload materials to ensure UI is in sync
      loadMaterials();
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getStatusBadge = (status: string) => {
    const statusStyles = {
      completed: 'bg-green-100 text-green-800',
      processing: 'bg-yellow-100 text-yellow-800',
      failed: 'bg-red-100 text-red-800',
      pending: 'bg-gray-100 text-gray-800',
    };

    return (
      <span
        className={`px-2 py-1 text-xs font-medium rounded-full ${
          statusStyles[status as keyof typeof statusStyles] || statusStyles.pending
        }`}
      >
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  // Get unique subjects and grades
  const subjects = Array.from(new Set(materials.map((m) => m.subject))).sort();
  const grades = Array.from(new Set(materials.map((m) => m.grade).filter((g): g is number => g !== undefined))).sort((a, b) => a - b);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-gray-600 hover:text-gray-900"
            >
              ← Back
            </button>
            <h1 className="text-2xl font-bold text-gray-900">Material Library</h1>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate('/materials/upload')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              + Upload Material
            </button>
            <button
              onClick={() => navigate('/exercises')}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              All Exercises
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by title, subject, or topic..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Subject Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Subject
              </label>
              <select
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Subjects</option>
                {subjects.map((subject) => (
                  <option key={subject} value={subject}>
                    {subject}
                  </option>
                ))}
              </select>
            </div>

            {/* Grade Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Grade Level
              </label>
              <select
                value={selectedGrade}
                onChange={(e) => setSelectedGrade(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Grades</option>
                {grades.map((grade) => (
                  <option key={grade} value={grade}>
                    Grade {grade}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Results Count */}
          <div className="mt-4 text-sm text-gray-600">
            Showing {filteredMaterials.length} of {materials.length} materials
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading materials...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Materials List */}
        {!loading && !error && (
          <div className="space-y-4">
            {filteredMaterials.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <svg
                  className="w-16 h-16 text-gray-400 mx-auto mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <p className="text-gray-600 text-lg mb-4">No materials found</p>
                <button
                  onClick={() => navigate('/materials/upload')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Upload your first material
                </button>
              </div>
            ) : (
              filteredMaterials.map((material) => (
                <div
                  key={material.id}
                  className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-start space-x-4">
                        {/* File Icon */}
                        <div className="flex-shrink-0">
                          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <svg
                              className="w-6 h-6 text-blue-600"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                              />
                            </svg>
                          </div>
                        </div>

                        {/* Material Info */}
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-semibold text-gray-900 mb-1">
                            {material.title}
                          </h3>
                          <div className="flex flex-wrap items-center gap-2 mb-2">
                            <span className="text-sm text-gray-600">
                              {material.subject}
                            </span>
                            {material.grade && (
                              <>
                                <span className="text-gray-400">•</span>
                                <span className="text-sm text-gray-600">
                                  Grade {material.grade}
                                </span>
                              </>
                            )}
                            <span className="text-gray-400">•</span>
                            <span className="text-sm text-gray-600">
                              {formatFileSize(material.file_size)}
                            </span>
                            {material.chunks_count && material.chunks_count > 0 && (
                              <>
                                <span className="text-gray-400">•</span>
                                <span className="text-sm text-gray-600">
                                  {material.chunks_count} chunks
                                </span>
                              </>
                            )}
                            <span className="text-gray-400">•</span>
                            {getStatusBadge(material.status)}
                          </div>

                          {/* Topics */}
                          {material.topics.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-2">
                              {material.topics.map((topic, index) => (
                                <span
                                  key={index}
                                  className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                                >
                                  {topic}
                                </span>
                              ))}
                            </div>
                          )}

                          <p className="text-sm text-gray-500">
                            Uploaded {formatDate(material.created_at)}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        onClick={() => navigate(`/materials/${material.id}`)}
                        className="px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg"
                      >
                        View
                      </button>
                      <button
                        onClick={() => handleDelete(material.id)}
                        className="px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </main>
    </div>
  );
}
