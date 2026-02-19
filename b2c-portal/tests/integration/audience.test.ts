/**
 * Integration tests for Audience CRUD operations.
 * Tests audience creation, management, and data operations.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import userEvent from '@testing-library/user-event';

import Audiences from '../../src/pages/Audiences';
import CreateAudienceDialog from '../../src/components/audiences/CreateAudienceDialog';

// Mock toast hook
vi.mock('../../src/hooks/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() })
}));

// Mock API responses
const server = setupServer(
  // Get audiences
  rest.get('/api/internal/audiences', (req, res, ctx) => {
    return res(ctx.json({
      success: true,
      audiences: [
        {
          id: 'aud_001',
          name: 'Healthcare Patients',
          description: 'Active patients for appointment reminders',
          size: 1250,
          status: 'active',
          created_at: '2024-01-15T10:00:00Z',
          updated_at: '2024-01-15T10:00:00Z',
          tenant_id: 'tenant_001',
          source: 'csv_upload',
          tags: ['healthcare', 'patients'],
          metadata: {
            columns: ['name', 'phone', 'email', 'appointment_date'],
            last_sync: '2024-01-15T10:00:00Z'
          }
        },
        {
          id: 'aud_002',
          name: 'Marketing Leads',
          description: 'Potential customers from marketing campaigns',
          size: 890,
          status: 'draft',
          created_at: '2024-01-14T15:30:00Z',
          updated_at: '2024-01-14T15:30:00Z',
          tenant_id: 'tenant_001',
          source: 'crm_sync',
          tags: ['marketing', 'leads'],
          metadata: {
            columns: ['name', 'phone', 'email', 'lead_source'],
            last_sync: '2024-01-14T15:30:00Z'
          }
        }
      ]
    }));
  }),

  // Create audience
  rest.post('/api/internal/audiences', (req, res, ctx) => {
    return res(ctx.json({
      success: true,
      audience: {
        id: 'aud_003',
        name: 'New Test Audience',
        description: 'Test audience for integration tests',
        size: 0,
        status: 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        tenant_id: 'tenant_001',
        source: 'manual',
        tags: ['test'],
        metadata: {
          columns: ['name', 'phone'],
          last_sync: null
        }
      }
    }));
  }),

  // Update audience
  rest.put('/api/internal/audiences/:id', (req, res, ctx) => {
    const { id } = req.params;
    return res(ctx.json({
      success: true,
      audience: {
        id,
        name: 'Updated Audience Name',
        description: 'Updated description',
        size: 1250,
        status: 'active',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: new Date().toISOString(),
        tenant_id: 'tenant_001',
        source: 'csv_upload',
        tags: ['updated', 'test'],
        metadata: {
          columns: ['name', 'phone', 'email'],
          last_sync: new Date().toISOString()
        }
      }
    }));
  }),

  // Delete audience
  rest.delete('/api/internal/audiences/:id', (req, res, ctx) => {
    return res(ctx.json({ success: true }));
  }),

  // Get audience by ID
  rest.get('/api/internal/audiences/:id', (req, res, ctx) => {
    const { id } = req.params;
    return res(ctx.json({
      success: true,
      audience: {
        id,
        name: 'Healthcare Patients',
        description: 'Active patients for appointment reminders',
        size: 1250,
        status: 'active',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
        tenant_id: 'tenant_001',
        source: 'csv_upload',
        tags: ['healthcare', 'patients'],
        metadata: {
          columns: ['name', 'phone', 'email', 'appointment_date'],
          last_sync: '2024-01-15T10:00:00Z'
        }
      }
    }));
  }),

  // Upload CSV
  rest.post('/api/internal/audiences/:id/upload', (req, res, ctx) => {
    return res(ctx.json({
      success: true,
      message: 'CSV uploaded successfully',
      processed_rows: 100,
      errors: []
    }));
  }),

  // Export audience
  rest.get('/api/internal/audiences/:id/export', (req, res, ctx) => {
    return res(
      ctx.set('Content-Type', 'text/csv'),
      ctx.set('Content-Disposition', 'attachment; filename="audience-export.csv"'),
      ctx.text('name,phone,email\nJohn Doe,+1234567890,john@example.com')
    );
  })
);

beforeEach(() => {
  server.listen();
});

afterEach(() => {
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Audience CRUD Integration Tests', () => {
  describe('Audiences List Page', () => {
    it('should render audiences list with search and filtering', async () => {
      renderWithRouter(<Audiences />);

      expect(screen.getByText('Audiences')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Search audiences...')).toBeInTheDocument();

      // Wait for audiences to load
      await waitFor(() => {
        expect(screen.getByText('Healthcare Patients')).toBeInTheDocument();
        expect(screen.getByText('Marketing Leads')).toBeInTheDocument();
      });

      // Check audience details
      expect(screen.getByText('1,250 contacts')).toBeInTheDocument();
      expect(screen.getByText('890 contacts')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Draft')).toBeInTheDocument();
    });

    it('should filter audiences by search term', async () => {
      renderWithRouter(<Audiences />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare Patients')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search audiences...');
      await userEvent.type(searchInput, 'healthcare');

      // Should filter results
      expect(screen.getByText('Healthcare Patients')).toBeInTheDocument();
      expect(screen.queryByText('Marketing Leads')).not.toBeInTheDocument();
    });

    it('should filter audiences by status', async () => {
      renderWithRouter(<Audiences />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare Patients')).toBeInTheDocument();
      });

      // Filter by active status
      const activeFilter = screen.getByText('Active');
      fireEvent.click(activeFilter);

      expect(screen.getByText('Healthcare Patients')).toBeInTheDocument();
      expect(screen.queryByText('Marketing Leads')).not.toBeInTheDocument();
    });

    it('should handle audience actions menu', async () => {
      renderWithRouter(<Audiences />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare Patients')).toBeInTheDocument();
      });

      // Click on more actions button
      const moreButton = screen.getAllByRole('button', { name: /more/i })[0];
      fireEvent.click(moreButton);

      // Should show menu options
      await waitFor(() => {
        expect(screen.getByText('View Details')).toBeInTheDocument();
        expect(screen.getByText('Edit')).toBeInTheDocument();
        expect(screen.getByText('Download')).toBeInTheDocument();
        expect(screen.getByText('Delete')).toBeInTheDocument();
      });
    });
  });

  describe('Create Audience', () => {
    it('should create new audience with form validation', async () => {
      const user = userEvent.setup();
      renderWithRouter(<CreateAudienceDialog open={true} onOpenChange={() => {}} />);

      // Fill in form
      const nameInput = screen.getByLabelText('Audience Name');
      const descriptionInput = screen.getByLabelText('Description');

      await user.type(nameInput, 'New Test Audience');
      await user.type(descriptionInput, 'Test audience for integration tests');

      // Select source
      const sourceSelect = screen.getByLabelText('Data Source');
      fireEvent.change(sourceSelect, { target: { value: 'manual' } });

      // Add tags
      const tagsInput = screen.getByLabelText('Tags');
      await user.type(tagsInput, 'test{enter}');

      // Submit form
      const createButton = screen.getByRole('button', { name: 'Create Audience' });
      fireEvent.click(createButton);

      // Should show success message
      await waitFor(() => {
        expect(screen.getByText('Audience created successfully')).toBeInTheDocument();
      });
    });

    it('should validate required fields', async () => {
      const user = userEvent.setup();
      renderWithRouter(<CreateAudienceDialog open={true} onOpenChange={() => {}} />);

      // Try to submit without filling required fields
      const createButton = screen.getByRole('button', { name: 'Create Audience' });
      fireEvent.click(createButton);

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText('Name is required')).toBeInTheDocument();
        expect(screen.getByText('Data source is required')).toBeInTheDocument();
      });
    });

    it('should handle API errors during creation', async () => {
      const user = userEvent.setup();
      
      // Mock API error
      server.use(
        rest.post('/api/internal/audiences', (req, res, ctx) => {
          return res(ctx.status(400), ctx.json({ detail: 'Audience name already exists' }));
        })
      );

      renderWithRouter(<CreateAudienceDialog open={true} onOpenChange={() => {}} />);

      // Fill form and submit
      const nameInput = screen.getByLabelText('Audience Name');
      await user.type(nameInput, 'Existing Audience');

      const sourceSelect = screen.getByLabelText('Data Source');
      fireEvent.change(sourceSelect, { target: { value: 'manual' } });

      const createButton = screen.getByRole('button', { name: 'Create Audience' });
      fireEvent.click(createButton);

      // Should show error message
      await waitFor(() => {
        expect(screen.getByText('Audience name already exists')).toBeInTheDocument();
      });
    });
  });

  describe('Update Audience', () => {
    it('should update audience information', async () => {
      const user = userEvent.setup();
      renderWithRouter(<Audiences />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare Patients')).toBeInTheDocument();
      });

      // Click edit button
      const moreButton = screen.getAllByRole('button', { name: /more/i })[0];
      fireEvent.click(moreButton);

      const editButton = screen.getByText('Edit');
      fireEvent.click(editButton);

      // Should open edit dialog
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Healthcare Patients')).toBeInTheDocument();
      });

      // Update name
      const nameInput = screen.getByDisplayValue('Healthcare Patients');
      await user.clear(nameInput);
      await user.type(nameInput, 'Updated Audience Name');

      // Submit update
      const saveButton = screen.getByRole('button', { name: 'Save Changes' });
      fireEvent.click(saveButton);

      // Should show success message
      await waitFor(() => {
        expect(screen.getByText('Audience updated successfully')).toBeInTheDocument();
      });
    });

    it('should handle update validation errors', async () => {
      const user = userEvent.setup();
      
      // Mock validation error
      server.use(
        rest.put('/api/internal/audiences/:id', (req, res, ctx) => {
          return res(ctx.status(400), ctx.json({ detail: 'Invalid audience data' }));
        })
      );

      renderWithRouter(<Audiences />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare Patients')).toBeInTheDocument();
      });

      // Open edit dialog and submit invalid data
      const moreButton = screen.getAllByRole('button', { name: /more/i })[0];
      fireEvent.click(moreButton);

      const editButton = screen.getByText('Edit');
      fireEvent.click(editButton);

      await waitFor(() => {
        const nameInput = screen.getByDisplayValue('Healthcare Patients');
        user.clear(nameInput);
      });

      const saveButton = screen.getByRole('button', { name: 'Save Changes' });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText('Invalid audience data')).toBeInTheDocument();
      });
    });
  });

  describe('Delete Audience', () => {
    it('should delete audience with confirmation', async () => {
      renderWithRouter(<Audiences />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare Patients')).toBeInTheDocument();
      });

      // Click delete button
      const moreButton = screen.getAllByRole('button', { name: /more/i })[0];
      fireEvent.click(moreButton);

      const deleteButton = screen.getByText('Delete');
      fireEvent.click(deleteButton);

      // Should show confirmation dialog
      await waitFor(() => {
        expect(screen.getByText('Are you sure you want to delete this audience?')).toBeInTheDocument();
      });

      // Confirm deletion
      const confirmButton = screen.getByRole('button', { name: 'Delete' });
      fireEvent.click(confirmButton);

      // Should show success message
      await waitFor(() => {
        expect(screen.getByText('Audience deleted successfully')).toBeInTheDocument();
      });
    });

    it('should handle delete API errors', async () => {
      // Mock API error
      server.use(
        rest.delete('/api/internal/audiences/:id', (req, res, ctx) => {
          return res(ctx.status(400), ctx.json({ detail: 'Cannot delete audience in use' }));
        })
      );

      renderWithRouter(<Audiences />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare Patients')).toBeInTheDocument();
      });

      // Attempt to delete
      const moreButton = screen.getAllByRole('button', { name: /more/i })[0];
      fireEvent.click(moreButton);

      const deleteButton = screen.getByText('Delete');
      fireEvent.click(deleteButton);

      const confirmButton = screen.getByRole('button', { name: 'Delete' });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText('Cannot delete audience in use')).toBeInTheDocument();
      });
    });
  });

  describe('CSV Upload and Export', () => {
    it('should handle CSV upload', async () => {
      renderWithRouter(<Audiences />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare Patients')).toBeInTheDocument();
      });

      // Click upload button
      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      // Should open upload dialog
      await waitFor(() => {
        expect(screen.getByText('Upload CSV Data')).toBeInTheDocument();
      });

      // Mock file upload
      const fileInput = screen.getByLabelText('CSV File');
      const file = new File(['name,phone\nJohn,123456'], 'test.csv', { type: 'text/csv' });
      
      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });

      fireEvent.change(fileInput);

      // Submit upload
      const uploadSubmitButton = screen.getByRole('button', { name: 'Upload' });
      fireEvent.click(uploadSubmitButton);

      await waitFor(() => {
        expect(screen.getByText('CSV uploaded successfully')).toBeInTheDocument();
        expect(screen.getByText('100 rows processed')).toBeInTheDocument();
      });
    });

    it('should handle CSV export', async () => {
      renderWithRouter(<Audiences />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare Patients')).toBeInTheDocument();
      });

      // Click export button
      const moreButton = screen.getAllByRole('button', { name: /more/i })[0];
      fireEvent.click(moreButton);

      const downloadButton = screen.getByText('Download');
      fireEvent.click(downloadButton);

      // Should initiate download
      await waitFor(() => {
        expect(screen.getByText('Export started')).toBeInTheDocument();
      });
    });
  });

  describe('Audience Statistics and Analytics', () => {
    it('should display audience statistics', async () => {
      renderWithRouter(<Audiences />);

      await waitFor(() => {
        expect(screen.getByText('Healthcare Patients')).toBeInTheDocument();
      });

      // Should show statistics cards
      expect(screen.getByText('Total Audiences')).toBeInTheDocument();
      expect(screen.getByText('Total Contacts')).toBeInTheDocument();
      expect(screen.getByText('Active Audiences')).toBeInTheDocument();
    });

    it('should show audience growth trends', async () => {
      renderWithRouter(<Audiences />);

      await waitFor(() => {
        expect(screen.getByText('Audience Growth')).toBeInTheDocument();
      });

      // Should display growth indicators
      expect(screen.getByText(/\+\d+%/)).toBeInTheDocument();
    });
  });

  describe('Real-time Updates', () => {
    it('should handle real-time audience size updates', async () => {
      renderWithRouter(<Audiences />);

      await waitFor(() => {
        expect(screen.getByText('1,250 contacts')).toBeInTheDocument();
      });

      // Simulate real-time update
      server.use(
        rest.get('/api/internal/audiences', (req, res, ctx) => {
          return res(ctx.json({
            audiences: [{
              id: 'aud_001',
              name: 'Healthcare Patients',
              size: 1251, // Updated size
              status: 'active',
              // ... other fields
            }]
          }));
        })
      );

      // Trigger refresh (this would normally be via WebSocket or polling)
      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(screen.getByText('1,251 contacts')).toBeInTheDocument();
      });
    });
  });
});