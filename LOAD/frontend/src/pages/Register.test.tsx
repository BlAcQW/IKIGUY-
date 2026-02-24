import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@test/helpers/render';

vi.mock('@/lib/auth', () => ({
  register: vi.fn(),
}));

import { RegisterPage } from './Register';
import { register } from '@/lib/auth';

const mockedRegister = vi.mocked(register);

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all four input fields', () => {
    render(<RegisterPage />);
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/organization/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('renders create account button', () => {
    render(<RegisterPage />);
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('renders link to login page', () => {
    render(<RegisterPage />);
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });

  it('submits and navigates on success', async () => {
    mockedRegister.mockResolvedValue({ userId: 'u1', organizationId: 'o1', role: 'OWNER' });

    const { user } = render(<RegisterPage />);

    await user.type(screen.getByLabelText(/full name/i), 'John Doe');
    await user.type(screen.getByLabelText(/organization/i), 'Acme');
    await user.type(screen.getByLabelText(/email/i), 'john@acme.com');
    await user.type(screen.getByLabelText(/password/i), 'secure123');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(mockedRegister).toHaveBeenCalledWith('john@acme.com', 'secure123', 'John Doe', 'Acme');
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });
  });

  it('shows error on registration failure', async () => {
    mockedRegister.mockRejectedValue(new Error('Email already exists'));

    const { user } = render(<RegisterPage />);

    await user.type(screen.getByLabelText(/full name/i), 'John');
    await user.type(screen.getByLabelText(/organization/i), 'Org');
    await user.type(screen.getByLabelText(/email/i), 'john@acme.com');
    await user.type(screen.getByLabelText(/password/i), 'password');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument();
    });
  });

  it('shows loading state during submission', async () => {
    mockedRegister.mockReturnValue(new Promise(() => {}));

    const { user } = render(<RegisterPage />);

    await user.type(screen.getByLabelText(/full name/i), 'John');
    await user.type(screen.getByLabelText(/organization/i), 'Org');
    await user.type(screen.getByLabelText(/email/i), 'a@b.com');
    await user.type(screen.getByLabelText(/password/i), 'password');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/creating account/i)).toBeInTheDocument();
    });
  });

  it('shows generic error for non-Error exceptions', async () => {
    mockedRegister.mockRejectedValue({ code: 'UNKNOWN' });

    const { user } = render(<RegisterPage />);

    await user.type(screen.getByLabelText(/full name/i), 'J');
    await user.type(screen.getByLabelText(/organization/i), 'O');
    await user.type(screen.getByLabelText(/email/i), 'a@b.com');
    await user.type(screen.getByLabelText(/password/i), 'password');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText('Registration failed')).toBeInTheDocument();
    });
  });

  it('renders page title', () => {
    render(<RegisterPage />);
    expect(screen.getByText('Create your account')).toBeInTheDocument();
  });
});
