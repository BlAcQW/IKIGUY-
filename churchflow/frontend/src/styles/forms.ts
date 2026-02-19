/**
 * Compact, Modern Form Styles
 *
 * Reusable Tailwind CSS classes for consistent form styling across ChurchFlow.
 * All forms use these standardized compact, beautiful, and modern styles.
 */

export const formStyles = {
  // Container styles
  container: {
    modal: "px-6 py-4 space-y-4",  // Compact modal form container
    page: "space-y-6 max-w-4xl mx-auto",  // Page form container
  },

  // Form field group wrapper
  fieldGroup: "group",

  // Label styles
  label: {
    base: "block text-xs font-semibold text-gray-700 mb-1.5",
    withIcon: "flex items-center gap-1.5",
    required: "text-xs font-semibold text-gray-700 mb-1.5 flex items-center gap-1.5",
  },

  // Required asterisk
  required: "text-red-500",

  // Input styles
  input: {
    base: "w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all",
    error: "w-full px-3 py-2 text-sm border-2 border-red-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all",
    disabled: "w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed",
  },

  // Textarea styles
  textarea: {
    base: "w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all resize-none",
    error: "w-full px-3 py-2 text-sm border-2 border-red-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all resize-none",
  },

  // Select/dropdown styles
  select: {
    base: "w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all appearance-none bg-white cursor-pointer",
    error: "w-full px-3 py-2 text-sm border-2 border-red-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all appearance-none bg-white cursor-pointer",
  },

  // Checkbox styles
  checkbox: {
    base: "w-3.5 h-3.5 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500",
    label: "text-xs text-gray-700",
    wrapper: "flex items-center gap-2 cursor-pointer hover:bg-gray-50 px-2 py-1 rounded transition-colors",
  },

  // Radio styles
  radio: {
    base: "w-3.5 h-3.5 text-indigo-600 focus:ring-2 focus:ring-indigo-500",
    label: "text-xs text-gray-700",
    wrapper: "flex items-center gap-2 cursor-pointer hover:bg-gray-50 px-2 py-1 rounded transition-colors",
  },

  // Button styles
  button: {
    // Primary action buttons
    primary: "px-4 py-2 text-sm bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 font-medium shadow-md shadow-indigo-500/30 hover:shadow-lg hover:shadow-indigo-500/40 flex items-center gap-2",

    // Secondary/cancel buttons
    secondary: "px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-medium",

    // Danger/destructive buttons
    danger: "px-4 py-2 text-sm bg-gradient-to-r from-red-600 to-red-700 text-white rounded-lg hover:from-red-700 hover:to-red-800 transition-all duration-200 font-medium shadow-md shadow-red-500/30 hover:shadow-lg hover:shadow-red-500/40 flex items-center gap-2",

    // Success/confirm buttons
    success: "px-4 py-2 text-sm bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all duration-200 font-medium shadow-md shadow-green-500/30 hover:shadow-lg hover:shadow-green-500/40 flex items-center gap-2",

    // Outline buttons
    outline: "px-4 py-2 text-sm border-2 border-indigo-600 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-all duration-200 font-medium",

    // Ghost buttons
    ghost: "px-4 py-2 text-sm text-gray-600 rounded-lg hover:bg-gray-100 transition-all duration-200 font-medium",

    // Disabled buttons
    disabled: "px-4 py-2 text-sm bg-gray-300 text-gray-500 rounded-lg cursor-not-allowed font-medium",
  },

  // Helper text styles
  helper: {
    base: "text-xs text-gray-500 mt-1",
    error: "text-xs text-red-600 mt-1",
    success: "text-xs text-green-600 mt-1",
  },

  // Modal styles
  modal: {
    overlay: "fixed inset-0 bg-gradient-to-br from-gray-900/80 to-gray-950/90 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200",
    container: "bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden animate-in slide-in-from-bottom-4 duration-300",
    header: "relative bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 px-6 py-6",
    headerPattern: "absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMC41Ii8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-20",
    headerContent: "relative flex items-center gap-4",
    headerIcon: "p-3 bg-white/20 backdrop-blur-sm rounded-xl",
    headerTitle: "text-2xl font-bold text-white",
    headerSubtitle: "text-indigo-100 text-sm mt-1",
    body: "overflow-y-auto max-h-[calc(90vh-180px)] px-6 py-4 space-y-4",
    footer: "sticky bottom-0 bg-gradient-to-t from-gray-50 to-white border-t border-gray-200 px-6 py-4 flex justify-between items-center gap-3",
  },

  // Card styles for forms
  card: {
    base: "bg-white rounded-xl shadow-sm border border-gray-200 p-6",
    hover: "bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200",
  },

  // Section header styles
  section: {
    title: "text-base font-semibold text-gray-900 mb-3",
    subtitle: "text-sm text-gray-600 mb-4",
    divider: "border-t border-gray-200 my-4",
  },

  // Grid layouts for forms
  grid: {
    cols1: "grid grid-cols-1 gap-4",
    cols2: "grid grid-cols-1 md:grid-cols-2 gap-4",
    cols3: "grid grid-cols-1 md:grid-cols-3 gap-4",
  },

  // File upload styles
  fileUpload: {
    dropzone: "border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-500 transition-colors cursor-pointer",
    dropzoneActive: "border-2 border-dashed border-indigo-500 bg-indigo-50 rounded-lg p-6 text-center",
    input: "hidden",
  },

  // Badge/tag styles
  badge: {
    default: "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800",
    primary: "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800",
    success: "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800",
    warning: "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800",
    danger: "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800",
  },
};

// Utility function to combine form styles
export const cn = (...classes: (string | undefined | null | false)[]) => {
  return classes.filter(Boolean).join(' ');
};
