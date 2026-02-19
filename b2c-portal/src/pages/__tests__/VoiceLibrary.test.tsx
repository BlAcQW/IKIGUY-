import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import VoiceLibrary from '../VoiceLibrary';

// Mock the navigate function
const mockNavigate = vi.fn();

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('VoiceLibrary', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
  });

  it('renders the Voice Library interface', () => {
    renderWithRouter(<VoiceLibrary />);
    
    expect(screen.getByText('Voice Library')).toBeInTheDocument();
    expect(screen.getByText('Featured Voices')).toBeInTheDocument();
    expect(screen.getByText('Explore all voices')).toBeInTheDocument();
  });

  it('displays featured voices', () => {
    renderWithRouter(<VoiceLibrary />);
    
    expect(screen.getByText('Road Dawg')).toBeInTheDocument();
    expect(screen.getByText('Aurora')).toBeInTheDocument();
    expect(screen.getByText('Mady')).toBeInTheDocument();
    expect(screen.getByText('vits-ara-1')).toBeInTheDocument();
  });

  it('displays voice grid with all voices', () => {
    renderWithRouter(<VoiceLibrary />);
    
    expect(screen.getByText('Will')).toBeInTheDocument();
    expect(screen.getByText('Jessica')).toBeInTheDocument();
    expect(screen.getByText('Clyde')).toBeInTheDocument();
    expect(screen.getByText('Jeremy')).toBeInTheDocument();
    expect(screen.getByText('Serena')).toBeInTheDocument();
    expect(screen.getByText('Domi')).toBeInTheDocument();
  });

  it('shows action buttons', () => {
    renderWithRouter(<VoiceLibrary />);
    
    expect(screen.getByText('Clone')).toBeInTheDocument();
    expect(screen.getByText('+ Add')).toBeInTheDocument();
    expect(screen.getByText('Sync')).toBeInTheDocument();
  });

  it('opens clone modal when clone button is clicked', () => {
    renderWithRouter(<VoiceLibrary />);
    
    const cloneButtons = screen.getAllByText('Clone');
    fireEvent.click(cloneButtons[0]); // Click the first clone button
    
    expect(screen.getByText('Clone Voice')).toBeInTheDocument();
  });

  it('opens create voice modal when + Add button is clicked', () => {
    renderWithRouter(<VoiceLibrary />);
    
    const addButton = screen.getByText('+ Add');
    fireEvent.click(addButton);
    
    expect(screen.getByText('Create New Voice')).toBeInTheDocument();
  });

  it('opens sync modal when sync button is clicked', () => {
    renderWithRouter(<VoiceLibrary />);
    
    const syncButton = screen.getByText('Sync');
    fireEvent.click(syncButton);
    
    expect(screen.getByText('Sync Voices')).toBeInTheDocument();
  });

  it('filters voices by search term', () => {
    renderWithRouter(<VoiceLibrary />);
    
    const searchInput = screen.getByPlaceholderText('Search by keyword, id, use...');
    fireEvent.change(searchInput, { target: { value: 'Road' } });
    
    expect(screen.getByText('Road Dawg')).toBeInTheDocument();
    expect(screen.queryByText('Aurora')).not.toBeInTheDocument();
  });

  it('displays voice information correctly', () => {
    renderWithRouter(<VoiceLibrary />);
    
    // Check for pricing information
    expect(screen.getAllByText('$0.036/min')).toHaveLength(expect.any(Number));
    
    // Check for latency information
    expect(screen.getAllByText('~400 ms')).toHaveLength(expect.any(Number));
    
    // Check for provider information
    expect(screen.getByText('11LABS')).toBeInTheDocument();
    expect(screen.getByText('PLAYHT')).toBeInTheDocument();
    expect(screen.getByText('NEETS')).toBeInTheDocument();
  });

  it('shows best for tags on featured voices', () => {
    renderWithRouter(<VoiceLibrary />);
    
    // Check for some of the tags that should be present
    expect(screen.getByText('Conversational')).toBeInTheDocument();
    expect(screen.getByText('Healthcare')).toBeInTheDocument();
    expect(screen.getByText('British')).toBeInTheDocument();
    expect(screen.getByText('Support')).toBeInTheDocument();
    expect(screen.getByText('Friendly')).toBeInTheDocument();
    expect(screen.getByText('Arabic')).toBeInTheDocument();
  });

  it('has working filter dropdowns', () => {
    renderWithRouter(<VoiceLibrary />);
    
    // Check that the select elements exist
    const selects = screen.getAllByRole('combobox');
    expect(selects).toHaveLength(3);
    
    // Check for specific options
    expect(screen.getByText('All Providers')).toBeInTheDocument();
    expect(screen.getByText('Select Gender')).toBeInTheDocument();
    expect(screen.getByText('Select Accent')).toBeInTheDocument();
  });

  it('displays voice ratings', () => {
    renderWithRouter(<VoiceLibrary />);
    
    // Check for star ratings (they should be present in the voice cards)
    const starElements = screen.getAllByText('4.');
    expect(starElements.length).toBeGreaterThan(0);
  });
});
