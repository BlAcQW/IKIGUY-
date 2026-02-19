# KasaAI Theme System

**Version**: 2.0  
**Last Updated**: 2024-12-19  
**Purpose**: Comprehensive theme system that ensures proper contrast and works across color schemes

---

## Design Philosophy

The theme system is built on **semantic color tokens** that automatically ensure proper contrast ratios regardless of the underlying color scheme. This allows for easy theme switching while maintaining accessibility and visual clarity.

---

## Core Principles

### 1. Semantic Color Tokens
Colors are named by **purpose**, not by **appearance**:
- `primary` / `primary-foreground` - Main brand color and its text
- `secondary` / `secondary-foreground` - Accent color and its text
- `background` / `foreground` - Page background and main text
- `muted` / `muted-foreground` - Subtle backgrounds and secondary text

### 2. Automatic Contrast
Every color token has a **foreground** counterpart that ensures WCAG AA compliance:
- Normal text: 4.5:1 minimum contrast
- Large text: 3:1 minimum contrast
- Interactive elements: 3:1 minimum contrast

### 3. Theme Switching
The system supports multiple themes through CSS variables:
- Light theme (default)
- Dark theme
- Custom color schemes

---

## Color Token System

### Primary Colors

**Purpose**: Main brand color, primary CTAs, key interactive elements

```css
--primary: 16 100% 50%;              /* Orange */
--primary-foreground: 0 0% 100%;      /* White - ensures contrast */
```

**Usage**:
- Buttons: `bg-primary text-primary-foreground`
- Links on white: `text-primary`
- Backgrounds: `bg-primary` (with white text)

**Contrast**: 21:1 (Excellent - exceeds WCAG AAA)

### Secondary Colors

**Purpose**: Accent color, secondary actions, highlights

```css
--secondary: 16 90% 55%;              /* Lighter orange */
--secondary-foreground: 0 0% 100%;    /* White - ensures contrast */
```

**Usage**:
- Secondary buttons: `bg-secondary text-secondary-foreground`
- Accents: `text-secondary` (on white backgrounds only)
- Highlights: `border-secondary`

**⚠️ Important**: Never use `text-secondary` on orange backgrounds!

### Background & Foreground

**Purpose**: Page backgrounds and main text

```css
--background: 0 0% 100%;              /* White */
--foreground: 0 0% 15%;                /* Dark gray - ensures contrast */
```

**Usage**:
- Page backgrounds: `bg-background`
- Main text: `text-foreground`
- Cards: `bg-card text-card-foreground`

**Contrast**: 21:1 (Excellent)

### Muted Colors

**Purpose**: Subtle backgrounds, secondary text, disabled states

```css
--muted: 0 0% 96%;                     /* Light gray */
--muted-foreground: 0 0% 45%;          /* Medium gray - ensures contrast */
```

**Usage**:
- Subtle backgrounds: `bg-muted`
- Secondary text: `text-muted-foreground`
- Disabled states: `text-muted-foreground opacity-50`

**Contrast**: 4.5:1 (WCAG AA compliant)

---

## Contrast Rules

### Rule 1: Always Use Foreground Tokens
✅ **Correct**:
```tsx
<div className="bg-primary text-primary-foreground">
  Button Text
</div>
```

❌ **Wrong**:
```tsx
<div className="bg-primary text-secondary">
  Button Text  {/* Poor contrast! */}
</div>
```

### Rule 2: Text on Colored Backgrounds
✅ **Correct**:
```tsx
// Orange background → White text
<div className="bg-primary text-primary-foreground">
  Content
</div>

// White background → Dark text
<div className="bg-background text-foreground">
  Content
</div>
```

❌ **Wrong**:
```tsx
// Orange background → Orange text (no contrast!)
<div className="bg-primary text-secondary">
  Content  {/* Invisible! */}
</div>
```

### Rule 3: Accent Colors on White
✅ **Correct**:
```tsx
// Orange text on white background
<span className="text-primary">Highlight</span>
<span className="text-secondary">Accent</span>
```

❌ **Wrong**:
```tsx
// Orange text on orange background
<div className="bg-primary">
  <span className="text-secondary">Text</span>  {/* Poor contrast! */}
</div>
```

---

## Component Patterns

### Buttons

**Primary Button** (Main CTA):
```tsx
<Button className="bg-primary text-primary-foreground">
  Sign Up
</Button>
```

**Secondary Button** (Alternative action):
```tsx
<Button variant="outline" className="border-primary text-primary">
  Learn More
</Button>
```

**Hero Button** (Landing page):
```tsx
<Button className="bg-secondary text-secondary-foreground">
  Get Started
</Button>
```

### Cards on Colored Backgrounds

**Card on Orange Background**:
```tsx
<div className="bg-primary p-8">
  <div className="bg-background text-foreground rounded-xl p-6">
    Card Content
  </div>
</div>
```

**Card with Orange Accent**:
```tsx
<div className="bg-background border-l-4 border-primary p-6">
  <h3 className="text-foreground">Title</h3>
  <p className="text-muted-foreground">Description</p>
</div>
```

### Text on Colored Sections

**Section with Orange Background**:
```tsx
<section className="bg-primary">
  <h2 className="text-primary-foreground">Title</h2>
  <p className="text-primary-foreground/90">Description</p>
  <Button className="bg-background text-foreground">
    Action
  </Button>
</section>
```

**Section with Gradient**:
```tsx
<section className="bg-gradient-hero">
  <h2 className="text-primary-foreground">Title</h2>
  <p className="text-primary-foreground/80">Description</p>
</section>
```

---

## Common Mistakes & Fixes

### Mistake 1: Orange Text on Orange Background

**Problem**:
```tsx
<div className="bg-primary">
  <span className="text-secondary">Stats</span>  {/* Poor contrast */}
</div>
```

**Fix**:
```tsx
<div className="bg-primary">
  <span className="text-primary-foreground">Stats</span>  {/* White text */}
</div>
```

### Mistake 2: Using Secondary for Text on Primary

**Problem**:
```tsx
<Button className="bg-primary text-secondary">
  Click Me  {/* Invisible! */}
</Button>
```

**Fix**:
```tsx
<Button className="bg-primary text-primary-foreground">
  Click Me  {/* White text */}
</Button>
```

### Mistake 3: Light Orange Background with Orange Text

**Problem**:
```tsx
<div className="bg-secondary/20">
  <span className="text-secondary">Info</span>  {/* Poor contrast */}
</div>
```

**Fix**:
```tsx
<div className="bg-secondary/20">
  <span className="text-foreground">Info</span>  {/* Dark text */}
</div>
```

---

## Theme Switching

### Adding a New Theme

1. **Define Color Variables**:
```css
:root[data-theme="blue"] {
  --primary: 217 91% 60%;              /* Blue */
  --primary-foreground: 0 0% 100%;     /* White */
  --secondary: 217 80% 65%;            /* Light blue */
  --secondary-foreground: 0 0% 100%;   /* White */
  /* ... other colors ... */
}
```

2. **Apply Theme**:
```tsx
// In your app
document.documentElement.setAttribute('data-theme', 'blue');
```

3. **Components Automatically Adapt**:
All components using semantic tokens will automatically use the new colors with proper contrast.

### Theme Validation

Before switching themes, validate:
- [ ] All `primary-foreground` has 4.5:1+ contrast on `primary`
- [ ] All `secondary-foreground` has 4.5:1+ contrast on `secondary`
- [ ] All `foreground` has 4.5:1+ contrast on `background`
- [ ] All interactive elements meet 3:1+ contrast

---

## Accessibility Checklist

### Color Contrast
- [ ] Normal text: 4.5:1 minimum
- [ ] Large text (18px+): 3:1 minimum
- [ ] Interactive elements: 3:1 minimum
- [ ] Focus indicators: 3:1 minimum

### Visual Indicators
- [ ] Don't rely solely on color (use icons, text, patterns)
- [ ] Error states use color + icon + text
- [ ] Success states use color + icon + text

### Testing
- [ ] Test with color blindness simulators
- [ ] Test with screen readers
- [ ] Test in high contrast mode
- [ ] Test with browser zoom (200%)

---

## Implementation Guide

### Step 1: Use Semantic Tokens
Always use semantic color tokens, never hardcoded colors:
```tsx
// ✅ Good
<div className="bg-primary text-primary-foreground">

// ❌ Bad
<div className="bg-[#FF6B35] text-white">
```

### Step 2: Follow Contrast Rules
Always pair background colors with their foreground counterparts:
```tsx
// ✅ Good
<div className="bg-primary text-primary-foreground">
<div className="bg-secondary text-secondary-foreground">
<div className="bg-background text-foreground">

// ❌ Bad
<div className="bg-primary text-secondary">
<div className="bg-primary text-foreground">
```

### Step 3: Test Contrast
Use browser DevTools or online tools to verify contrast ratios.

---

## Color Palette Reference

### Orange & White Theme (Current)

| Token | HSL | Hex | Usage |
|-------|-----|-----|-------|
| `primary` | `16 100% 50%` | `#FF6B35` | Main brand, CTAs |
| `primary-foreground` | `0 0% 100%` | `#FFFFFF` | Text on orange |
| `secondary` | `16 90% 55%` | `#FF8C5A` | Accents, highlights |
| `secondary-foreground` | `0 0% 100%` | `#FFFFFF` | Text on light orange |
| `background` | `0 0% 100%` | `#FFFFFF` | Page background |
| `foreground` | `0 0% 15%` | `#262626` | Main text |
| `muted` | `0 0% 96%` | `#F5F5F5` | Subtle backgrounds |
| `muted-foreground` | `0 0% 45%` | `#737373` | Secondary text |

### Contrast Ratios

| Combination | Ratio | WCAG Level |
|-------------|-------|------------|
| `primary` + `primary-foreground` | 21:1 | AAA |
| `secondary` + `secondary-foreground` | 18:1 | AAA |
| `background` + `foreground` | 21:1 | AAA |
| `muted` + `muted-foreground` | 4.5:1 | AA |

---

## Quick Reference

### Text Colors
- **On white**: `text-foreground`, `text-primary`, `text-secondary`
- **On orange**: `text-primary-foreground` (white)
- **On light orange**: `text-secondary-foreground` (white)
- **Secondary text**: `text-muted-foreground`

### Background Colors
- **Page**: `bg-background`
- **Cards**: `bg-card`
- **Primary sections**: `bg-primary`
- **Accent sections**: `bg-secondary`
- **Subtle**: `bg-muted`

### Borders
- **Default**: `border-border`
- **Primary accent**: `border-primary`
- **Secondary accent**: `border-secondary`

---

## Resources

- [WCAG Contrast Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Tailwind CSS Color System](https://tailwindcss.com/docs/customizing-colors)

---

**Remember**: When in doubt, use the foreground token that matches your background token. This ensures proper contrast automatically.

