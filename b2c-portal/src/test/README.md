# B2C Portal Unit Testing

This directory contains the comprehensive unit testing setup for the B2C Portal application.

## Overview

The testing infrastructure is built with:

- **Vitest** - Fast unit test runner
- **React Testing Library** - Component testing utilities
- **MSW (Mock Service Worker)** - API mocking
- **Custom test utilities** - Reusable test helpers

## Directory Structure

```
src/test/
├── setup.ts                 # Global test setup and mocks
├── utils/
│   └── test-utils.tsx       # Custom render function and test helpers
├── mocks/
│   ├── api-mocks.ts         # API client mocks
│   └── hooks-mocks.ts       # React hooks mocks
├── __tests__/               # Test files (mirrors src structure)
│   ├── components/          # Component tests
│   ├── hooks/              # Hook tests
│   ├── lib/                # Utility tests
│   └── pages/              # Page tests
└── README.md               # This file
```

## Quick Start

### Running Tests

```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# Run specific test categories
npm run test:components
npm run test:hooks
npm run test:lib

# Run tests with UI
npm run test:ui
```

### Writing Tests

1. **Component Tests**: Test React components with user interactions
2. **Hook Tests**: Test custom React hooks
3. **Utility Tests**: Test pure functions and utilities
4. **Integration Tests**: Test component interactions

## Test Utilities

### Custom Render Function

```tsx
import { render, screen } from '@/test/utils/test-utils';

// Render with all providers
render(<MyComponent />);

// Render without router
render(<MyComponent />, { withRouter: false });

// Render with custom query client
const queryClient = new QueryClient();
render(<MyComponent />, { queryClient });
```

### Mock Data Factories

```tsx
import {
  createMockAssistant,
  createMockCampaign,
} from '@/test/utils/test-utils';

const assistant = createMockAssistant({ name: 'Custom Assistant' });
const campaign = createMockCampaign({ status: 'active' });
```

### API Mocking

```tsx
import { mockApiResponse, mockApiError } from '@/test/utils/test-utils';

// Mock successful response
global.fetch = vi.fn().mockResolvedValue(mockApiResponse({ data: 'success' }));

// Mock error response
global.fetch = vi.fn().mockResolvedValue(mockApiError(500, 'Server Error'));
```

### Form Testing Helpers

```tsx
import {
  fillFormField,
  selectOption,
  clickButton,
} from '@/test/utils/test-utils';

// Fill form fields
await fillFormField('Name', 'John Doe');

// Select dropdown options
await selectOption('Type', 'Customer Support');

// Click buttons
await clickButton('Submit');
```

## Test Patterns

### Component Testing

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@/test/utils/test-utils';
import { MyComponent } from '@/components/MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('handles user interactions', async () => {
    render(<MyComponent />);

    await fillFormField('Name', 'John');
    await clickButton('Submit');

    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument();
    });
  });

  it('shows loading state', () => {
    render(<MyComponent isLoading={true} />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('shows error state', () => {
    render(<MyComponent error='Something went wrong' />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });
});
```

### Hook Testing

```tsx
import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useMyHook } from '@/hooks/useMyHook';

describe('useMyHook', () => {
  it('returns initial state', () => {
    const { result } = renderHook(() => useMyHook());
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(true);
  });

  it('fetches data successfully', async () => {
    global.fetch = vi.fn().mockResolvedValue(mockApiResponse({ data: 'test' }));

    const { result } = renderHook(() => useMyHook());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBe('test');
  });
});
```

### API Testing

```tsx
import { describe, it, expect, vi } from 'vitest';
import { assistantApi } from '@/lib/core-api';

describe('assistantApi', () => {
  it('creates assistant successfully', async () => {
    const mockAssistant = createMockAssistant();

    global.fetch = vi.fn().mockResolvedValue(mockApiResponse(mockAssistant));

    const result = await assistantApi.create(mockAssistant);

    expect(result).toEqual(mockAssistant);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/internal/assistants'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(mockAssistant),
      })
    );
  });

  it('handles API errors', async () => {
    global.fetch = vi.fn().mockResolvedValue(mockApiError(500, 'Server Error'));

    await expect(assistantApi.create({})).rejects.toThrow('Server Error');
  });
});
```

## Mocking Strategy

### API Mocks

- Use MSW for API mocking in integration tests
- Use `global.fetch` mocking for unit tests
- Mock Supabase client for database operations

### Hook Mocks

- Mock React Query hooks for data fetching
- Mock React Router hooks for navigation
- Mock custom hooks for business logic

### Component Mocks

- Mock external dependencies
- Mock complex child components
- Use test IDs for reliable element selection

## Best Practices

### Test Organization

1. **Group related tests** using `describe` blocks
2. **Use descriptive test names** that explain the behavior
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **Test one thing per test** for better isolation

### Test Data

1. **Use factory functions** for consistent test data
2. **Override only necessary fields** in test data
3. **Use realistic data** that matches production
4. **Keep test data minimal** and focused

### Assertions

1. **Test user behavior** not implementation details
2. **Use semantic queries** (getByRole, getByLabelText)
3. **Avoid testing library internals**
4. **Test error states and edge cases**

### Performance

1. **Mock expensive operations** (API calls, file system)
2. **Use `vi.fn()`** for function mocks
3. **Clean up after tests** with `afterEach`
4. **Avoid unnecessary re-renders** in tests

## Coverage Goals

- **Components**: 90% line coverage
- **Hooks**: 95% line coverage
- **Utilities**: 100% line coverage
- **Overall**: 80% line coverage

## Debugging Tests

### Common Issues

1. **Async operations**: Use `waitFor` for async assertions
2. **Mock cleanup**: Reset mocks between tests
3. **Provider setup**: Ensure all required providers are wrapped
4. **Event handling**: Use `userEvent` for realistic interactions

### Debug Commands

```bash
# Run specific test file
npm test MyComponent.test.tsx

# Run tests with verbose output
npm test -- --verbose

# Run tests with UI for debugging
npm run test:ui

# Run tests with coverage report
npm run test:coverage
```

## Continuous Integration

Tests are automatically run in CI/CD pipeline:

1. **Pre-commit**: Run unit tests
2. **Pull Request**: Run all tests with coverage
3. **Main Branch**: Run full test suite

## Contributing

When adding new tests:

1. **Follow existing patterns** and conventions
2. **Add test coverage** for new features
3. **Update documentation** if needed
4. **Ensure tests pass** before submitting PR

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [MSW Documentation](https://mswjs.io/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
