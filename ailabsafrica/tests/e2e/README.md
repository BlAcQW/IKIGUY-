# E2E Testing with Playwright

This directory contains comprehensive end-to-end tests for the AI Labs Africa application using Playwright.

## 🚀 Quick Start

### Prerequisites

1. **Node.js** (v18 or higher)
2. **Playwright browsers** (installed automatically)
3. **Supabase environment** (configured with test database)

### Installation

```bash
# Install dependencies (if not already done)
npm install

# Install Playwright browsers
npm run test:e2e:install
```

### Running Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run tests with UI
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Run tests in debug mode
npm run test:e2e:debug

# Run specific test file
npx playwright test assistant-creation.spec.ts

# Run tests with specific browser
npx playwright test --project=chromium
```

## 📁 Test Structure

```
tests/e2e/
├── README.md                    # This file
├── utils/
│   └── test-helpers.ts         # Shared test utilities
├── fixtures/
│   └── test-document.txt       # Test files for uploads
├── assistant-creation.spec.ts  # Assistant creation flow tests
├── user-authentication.spec.ts # Authentication flow tests
├── template-configuration.spec.ts # Template configuration tests
├── database-integration.spec.ts # Database persistence tests
├── cross-component-integration.spec.ts # Cross-component tests
├── performance.spec.ts         # Performance tests
└── error-scenarios.spec.ts     # Error handling tests
```

## 🧪 Test Categories

### 1. Assistant Creation Flow (`assistant-creation.spec.ts`)
- ✅ Successful assistant creation
- ✅ Required field validation
- ✅ File upload for knowledge base
- ✅ Network error handling
- ✅ Auto-save progress functionality

### 2. User Authentication (`user-authentication.spec.ts`)
- ✅ Successful sign in/out
- ✅ Invalid credentials handling
- ✅ Required field validation
- ✅ Session timeout handling
- ✅ Password reset flow
- ✅ Email verification flow

### 3. Template Configuration (`template-configuration.spec.ts`)
- ✅ Configuration dialog opening
- ✅ Calendar integration setup
- ✅ Email integration setup
- ✅ Chat integrations (WhatsApp, SMS, Telegram, Slack)
- ✅ Helpdesk integrations (Freshdesk, Intercom, Zendesk)
- ✅ CRM integration setup
- ✅ Database integration setup
- ✅ Validation and error handling

### 4. Database Integration (`database-integration.spec.ts`)
- ✅ Data persistence verification
- ✅ Update operations
- ✅ Deletion operations
- ✅ Configuration persistence
- ✅ Concurrent operations
- ✅ Error handling and cleanup

### 5. Cross-Component Integration (`cross-component-integration.spec.ts`)
- ✅ Navigation state management
- ✅ Form state persistence
- ✅ Error boundary handling
- ✅ Global error state
- ✅ Authentication state across components
- ✅ Loading states
- ✅ Toast notifications
- ✅ Modal dialogs
- ✅ Search and filter state
- ✅ Responsive design
- ✅ Keyboard navigation
- ✅ Accessibility features

### 6. Performance Tests (`performance.spec.ts`)
- ✅ Page load performance
- ✅ Form submission performance
- ✅ Large dataset handling
- ✅ Search operation performance
- ✅ Concurrent operations
- ✅ Memory usage monitoring
- ✅ Network latency handling
- ✅ Database query optimization
- ✅ Asset loading efficiency
- ✅ Form validation performance

### 7. Error Scenarios (`error-scenarios.spec.ts`)
- ✅ Network error recovery
- ✅ Invalid data handling
- ✅ Session timeout
- ✅ Server errors
- ✅ API rate limiting
- ✅ Malformed responses
- ✅ Authentication errors
- ✅ Database connection errors
- ✅ File upload errors
- ✅ Concurrent modification errors
- ✅ Timeout errors
- ✅ Server validation errors

## 🛠️ Test Utilities

### TestDataManager
- `createTestUser()` - Create test user with credentials
- `cleanupTestUser(userId)` - Clean up test user
- `createTestAssistant(userId)` - Create test assistant
- `cleanupTestAssistant(assistantId)` - Clean up test assistant
- `getTestData(userId)` - Get all test data for user

### AuthHelpers
- `signIn(page, email, password)` - Sign in user via UI
- `signOut(page)` - Sign out user via UI
- `isAuthenticated(page)` - Check authentication status

### NavigationHelpers
- `goToDashboard(page)` - Navigate to dashboard
- `goToCreateAssistant(page)` - Navigate to create assistant
- `goToVoiceAgents(page)` - Navigate to voice agents
- `goToWallet(page)` - Navigate to wallet

### FormHelpers
- `fillField(page, testId, value)` - Fill form field
- `selectOption(page, testId, value)` - Select dropdown option
- `uploadFile(page, testId, filePath)` - Upload file
- `submitForm(page, testId)` - Submit form

### AssertionHelpers
- `isVisible(page, testId)` - Check element visibility
- `isNotVisible(page, testId)` - Check element not visible
- `hasText(page, testId, text)` - Check element text
- `containsText(page, testId, text)` - Check element contains text
- `toastShown(page, message)` - Check toast notification

### PerformanceHelpers
- `measurePageLoad(page, url)` - Measure page load time
- `measureFormSubmission(page, formTestId)` - Measure form submission time

## 🔧 Configuration

### Playwright Config (`playwright.config.ts`)
- **Test Directory**: `./tests/e2e`
- **Browsers**: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari
- **Base URL**: `http://localhost:5173`
- **Web Server**: Automatically starts dev server
- **Parallel Execution**: Enabled
- **Retries**: 2 on CI, 0 locally
- **Reporters**: HTML reporter

### Environment Variables
```bash
# Required for test data management
VITE_SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Optional
VITE_DEBUG_MODE=true
```

## 📊 Test Data Management

### Automatic Cleanup
- Test users are automatically created and cleaned up
- Test assistants are automatically created and cleaned up
- Database state is restored after each test suite

### Test Isolation
- Each test runs in isolation
- No shared state between tests
- Clean database state for each test

### Data Verification
- Tests verify data persistence in database
- Tests verify data updates and deletions
- Tests verify configuration persistence

## 🚨 Error Handling

### Network Errors
- Tests simulate network failures
- Verify error recovery mechanisms
- Test offline/online scenarios

### Server Errors
- Tests simulate 500, 503, 429 errors
- Verify proper error messages
- Test retry mechanisms

### Validation Errors
- Tests client-side validation
- Tests server-side validation
- Verify error message display

## 📈 Performance Monitoring

### Performance Budgets
- **Dashboard Load**: < 3 seconds
- **Create Assistant Page**: < 2 seconds
- **Form Submission**: < 5 seconds
- **Search Operations**: < 1 second
- **Memory Increase**: < 50MB

### Performance Metrics
- Page load times
- Form submission times
- Memory usage
- Network request times
- Asset loading times

## 🔍 Debugging

### Debug Mode
```bash
npm run test:e2e:debug
```

### Headed Mode
```bash
npm run test:e2e:headed
```

### UI Mode
```bash
npm run test:e2e:ui
```

### Specific Test
```bash
npx playwright test assistant-creation.spec.ts --debug
```

### Screenshots and Videos
- Screenshots on failure (automatic)
- Videos on failure (automatic)
- Trace files for debugging

## 📝 Writing New Tests

### Test Structure
```typescript
import { test, expect } from '@playwright/test';
import { TestDataManager, AuthHelpers, NavigationHelpers, FormHelpers, AssertionHelpers } from './utils/test-helpers';

test.describe('Feature Name', () => {
  let testUser: { email: string; password: string; userId: string };

  test.beforeAll(async () => {
    testUser = await TestDataManager.createTestUser();
  });

  test.afterAll(async () => {
    if (testUser?.userId) {
      await TestDataManager.cleanupTestUser(testUser.userId);
    }
  });

  test('should perform specific action', async ({ page }) => {
    // Arrange
    await AuthHelpers.signIn(page, testUser.email, testUser.password);
    
    // Act
    await NavigationHelpers.goToDashboard(page);
    
    // Assert
    await AssertionHelpers.isVisible(page, 'dashboard-content');
  });
});
```

### Best Practices
1. **Use test utilities** - Don't reinvent the wheel
2. **Clean up data** - Always clean up test data
3. **Test isolation** - Each test should be independent
4. **Meaningful assertions** - Test behavior, not implementation
5. **Error scenarios** - Test both success and failure cases
6. **Performance** - Include performance assertions where relevant

## 🚀 CI/CD Integration

### GitHub Actions
```yaml
- name: Run E2E Tests
  run: npm run test:e2e
```

### Environment Setup
- Install dependencies
- Install Playwright browsers
- Set up environment variables
- Start application
- Run tests
- Generate reports

## 📊 Reporting

### HTML Report
- Generated automatically after test run
- Located in `playwright-report/`
- Interactive test results
- Screenshots and videos
- Performance metrics

### Console Output
- Real-time test progress
- Performance metrics
- Error details
- Test summaries

## 🔧 Troubleshooting

### Common Issues

1. **Browser Installation**
   ```bash
   npx playwright install
   ```

2. **Environment Variables**
   - Ensure Supabase credentials are set
   - Check service role key permissions

3. **Database Access**
   - Verify RLS policies allow test operations
   - Check database connection

4. **Test Failures**
   - Check screenshots and videos
   - Review console output
   - Verify test data cleanup

### Debug Commands
```bash
# Install browsers
npx playwright install

# Show browser info
npx playwright --version

# Run with verbose output
npx playwright test --reporter=verbose

# Run specific browser
npx playwright test --project=chromium
```

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Test API](https://playwright.dev/docs/api/class-test)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Playwright Debugging](https://playwright.dev/docs/debug)

## 🤝 Contributing

When adding new tests:

1. Follow the existing test structure
2. Use the provided test utilities
3. Include both success and error scenarios
4. Add performance assertions where relevant
5. Update this README if adding new test categories
6. Ensure proper cleanup in afterAll hooks
