# Contrast Fixes - Orange Theme

**Date**: 2024-12-19  
**Issue**: Poor text contrast on orange backgrounds after theme change

---

## Problem Summary

After switching to orange/white theme, several components had poor text contrast:
- Orange text (`text-secondary`) on orange backgrounds (`bg-primary`, `bg-secondary`)
- Orange text on light orange backgrounds (`bg-secondary/10`, `bg-secondary/20`)

---

## Fixed Components

### 1. Auth Page (`src/pages/Auth.tsx`)

**Issues Found**:
- Line 346: `bg-secondary/20` with `text-secondary` (light orange bg + orange text)
- Lines 357, 361, 365: `text-secondary` on `bg-primary` (orange text on orange bg - invisible!)

**Fixes Applied**:
```tsx
// Before
<div className="bg-secondary/20">
  <BookOpen className="text-secondary" />
</div>
<div className="text-secondary">150K+</div>

// After
<div className="bg-primary-foreground/20">
  <BookOpen className="text-primary-foreground" />
</div>
<div className="text-primary-foreground">150K+</div>
```

### 2. Hero Component (`src/components/landing/Hero.tsx`)

**Issues Found**:
- Line 44: `text-secondary` on `bg-secondary/20` (poor contrast)

**Fixes Applied**:
```tsx
// Before
<div className="bg-secondary/20">
  <Sparkles className="text-secondary" />
</div>

// After
<div className="bg-primary-foreground/20">
  <Sparkles className="text-primary-foreground" />
</div>
```

### 3. Pricing Component (`src/components/landing/Pricing.tsx`)

**Issues Found**:
- Lines 153-154: `bg-secondary/10` and `bg-secondary/20` with `text-secondary`

**Fixes Applied**:
```tsx
// Before
className={`${
  plan.popular
    ? "bg-secondary/20 text-secondary"
    : "bg-secondary/10 text-secondary"
}`}

// After
className={`${
  plan.popular
    ? "bg-primary text-primary-foreground"
    : "bg-primary/10 text-primary"
}`}
```

---

## Contrast Rules Applied

### Rule 1: Text on Orange Backgrounds
✅ **Always use white text** (`text-primary-foreground` or `text-secondary-foreground`)

```tsx
// ✅ Correct
<div className="bg-primary text-primary-foreground">Text</div>
<div className="bg-secondary text-secondary-foreground">Text</div>

// ❌ Wrong
<div className="bg-primary text-secondary">Text</div>  {/* Invisible! */}
```

### Rule 2: Text on Light Orange Backgrounds
✅ **Use dark orange** (`text-primary`) or **white** (`text-primary-foreground`) depending on opacity

```tsx
// Light background (10-20% opacity) → Dark text
<div className="bg-primary/10 text-primary">Text</div>
<div className="bg-secondary/20 text-primary">Text</div>

// Medium background (30-50% opacity) → White text
<div className="bg-primary/30 text-primary-foreground">Text</div>
```

### Rule 3: Badges and Tags
✅ **Use proper contrast combinations**

```tsx
// ✅ Good - Orange text on white/light background
<span className="bg-primary/10 text-primary">Tag</span>

// ✅ Good - White text on orange background
<span className="bg-primary text-primary-foreground">Tag</span>

// ❌ Bad - Orange text on orange background
<span className="bg-primary text-secondary">Tag</span>
```

---

## Components Still Using `bg-secondary/10 text-secondary`

These are **safe** because they're on white backgrounds (not orange):

- `src/pages/Devotional.tsx` - Badges on white cards ✅
- `src/pages/Feed.tsx` - Category tags on white ✅
- `src/pages/Bookmarks.tsx` - Tags on white ✅
- `src/components/landing/TrendingDevotionals.tsx` - Tags on white ✅

**Note**: These work because `bg-secondary/10` creates a very light orange tint on white, and orange text on this is readable. However, for consistency, consider using `bg-primary/10 text-primary` instead.

---

## New Utility Classes Added

Added to `src/index.css`:

```css
/* Contrast-safe text on colored backgrounds */
.text-on-primary {
  @apply text-primary-foreground;
}

.text-on-secondary {
  @apply text-secondary-foreground;
}

/* Safe badge styles */
.badge-primary {
  @apply bg-primary/10 text-primary border border-primary/20;
}

.badge-secondary {
  @apply bg-secondary/10 text-primary border border-secondary/20;
}
```

---

## Testing Checklist

- [x] Auth page - Orange background section has white text
- [x] Hero section - Badge has proper contrast
- [x] Pricing component - Checkmarks have proper contrast
- [ ] All pages reviewed for contrast issues
- [ ] WCAG AA compliance verified (4.5:1 minimum)

---

## Remaining Work

### Optional Improvements
1. **Consistency**: Replace `bg-secondary/10 text-secondary` with `bg-primary/10 text-primary` for consistency
2. **Badge Components**: Create reusable badge component with proper contrast
3. **Theme Testing**: Test with color blindness simulators

---

## Quick Reference

| Background | Text Color | Usage |
|------------|------------|-------|
| `bg-primary` | `text-primary-foreground` | Orange sections |
| `bg-secondary` | `text-secondary-foreground` | Light orange sections |
| `bg-primary/10` | `text-primary` | Light orange badges on white |
| `bg-primary/20` | `text-primary-foreground` | Medium orange overlays |
| `bg-background` | `text-foreground` | White pages |

---

**Status**: Critical contrast issues fixed  
**Next**: Build and deploy

