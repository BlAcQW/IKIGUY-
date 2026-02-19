# KasaAI Design System & UX Guidelines

**Version**: 1.0  
**Last Updated**: 2024-12-19  
**Author**: Senior UX/UI/Frontend Development Team

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Core Principles](#core-principles)
3. [Color System](#color-system)
4. [Typography](#typography)
5. [Layout & Spacing](#layout--spacing)
6. [Navigation](#navigation)
7. [Mobile Optimization](#mobile-optimization)
8. [Animations & Interactions](#animations--interactions)
9. [Call-to-Actions (CTAs)](#call-to-actions-ctas)
10. [Performance](#performance)
11. [Accessibility](#accessibility)
12. [Component Patterns](#component-patterns)
13. [Implementation Checklist](#implementation-checklist)

---

## Design Philosophy

### Vision Statement
Create **inspiring, engaging, and accessible** digital experiences that prioritize user needs while maintaining modern aesthetics and excellent performance. Every design decision should serve the user's journey and facilitate meaningful engagement.

### Core Values
1. **User-Centric**: Every design decision starts with the user's needs
2. **Clarity Over Cleverness**: Intuitive navigation beats complex interactions
3. **Performance First**: Fast, responsive experiences build trust
4. **Accessibility by Default**: Inclusive design is not optional
5. **Mobile-First**: Design for mobile, enhance for desktop
6. **Modern & Engaging**: Contemporary aesthetics that inspire action

### Inspiration Sources
- **North Point Community Church**: Clean, modern, vibrant orange/white theme
- **Deeper/Wider Initiative**: Engaging typography, clear messaging
- **Tithely Best Practices**: Easy navigation, clear CTAs, mobile optimization
- **Modern Church Websites**: Inspiring visuals, intuitive user flows

---

## Core Principles

Based on analysis of [leading church websites](https://get.tithe.ly/blog/5-examples-of-great-church-websites-and-why-we-think-theyre-awesome), these principles are non-negotiable:

### 1. Easy Navigation
**Principle**: Users should never have to think about where to find something.

**Guidelines**:
- Maximum 5-7 main navigation items
- Clear, descriptive labels (avoid jargon)
- Consistent navigation across all pages
- Breadcrumbs for deep navigation
- Search functionality prominently placed
- Mobile: Bottom navigation for primary actions

**Implementation**:
```tsx
// Primary Navigation Structure
const mainNav = [
  { label: "Home", path: "/", icon: Home },
  { label: "Devotionals", path: "/feed", icon: BookOpen },
  { label: "Groups", path: "/groups", icon: Users },
  { label: "Profile", path: "/profile", icon: User },
];
```

### 2. Clear Calls-to-Action (CTAs)
**Principle**: Every page should guide users to the next meaningful action.

**Guidelines**:
- One primary CTA per page/section
- Use action-oriented language: "Join Us Sunday", "Watch Sermon", "Get Started"
- High contrast buttons (primary color)
- Prominent placement (above fold when possible)
- Mobile: Full-width buttons for easy tapping (min 44x44px)

**CTA Hierarchy**:
- **Primary**: Main action (orange background, white text)
- **Secondary**: Alternative action (outline, orange border)
- **Tertiary**: Less important (text link, subtle)

**Examples**:
```tsx
// Primary CTA
<Button className="bg-primary text-primary-foreground w-full md:w-auto">
  Join Us This Sunday
</Button>

// Secondary CTA
<Button variant="outline" className="border-primary text-primary">
  Watch Online
</Button>
```

### 3. Aesthetic Excellence
**Principle**: Beautiful design builds trust and engagement.

**Guidelines**:
- Clean, uncluttered layouts
- Generous white space
- High-quality imagery (optimized, relevant)
- Consistent visual hierarchy
- Modern, contemporary feel
- Avoid: Busy backgrounds, too many colors, cluttered layouts

### 4. Mobile Optimization
**Principle**: Mobile is not an afterthought—it's the primary experience.

**Guidelines**:
- **Mobile-First Design**: Design for 320px width, enhance for larger screens
- **Touch Targets**: Minimum 44x44px for all interactive elements
- **Readable Text**: Minimum 16px font size, 1.5 line height
- **Fast Loading**: < 3 seconds on 3G connection
- **Thumb-Friendly**: Primary actions within thumb reach zone
- **Responsive Images**: Use `srcset` and modern formats (WebP, AVIF)

**Breakpoints**:
```css
/* Mobile First Approach */
.container {
  padding: 1rem; /* Mobile */
}

@media (min-width: 640px) { /* sm */
  .container { padding: 1.5rem; }
}

@media (min-width: 768px) { /* md */
  .container { padding: 2rem; }
}

@media (min-width: 1024px) { /* lg */
  .container { padding: 2.5rem; }
}
```

### 5. Performance
**Principle**: Speed is a feature, not a nice-to-have.

**Targets**:
- **First Contentful Paint (FCP)**: < 1.8s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Time to Interactive (TTI)**: < 3.8s
- **Cumulative Layout Shift (CLS)**: < 0.1

**Optimization Strategies**:
- Code splitting and lazy loading
- Image optimization (WebP, lazy loading)
- Font subsetting and preloading
- Service worker caching
- Minimal JavaScript bundles

---

## Color System

### Primary Palette: Orange & White (North Point Inspired)

**Primary Orange**:
- **Main**: `hsl(16 100% 50%)` - `#FF6B35`
- **Light**: `hsl(16 90% 65%)` - For hover states
- **Dark**: `hsl(16 100% 40%)` - For pressed states
- **Subtle**: `hsl(16 50% 95%)` - For backgrounds

**Neutrals**:
- **Background**: `hsl(0 0% 100%)` - Pure white
- **Foreground**: `hsl(0 0% 15%)` - Dark text
- **Muted**: `hsl(0 0% 96%)` - Light backgrounds
- **Border**: `hsl(0 0% 90%)` - Subtle borders

**Semantic Colors**:
- **Success**: `hsl(142 76% 36%)` - Green
- **Warning**: `hsl(38 92% 50%)` - Amber
- **Error**: `hsl(0 84% 60%)` - Red
- **Info**: `hsl(199 89% 48%)` - Blue

### Usage Guidelines

**Primary Orange**:
- Use for primary CTAs, links, and key interactive elements
- Maintains high contrast (WCAG AA) on white backgrounds
- Avoid on orange backgrounds (use white text)

**White Backgrounds**:
- Primary background for all pages
- Ensures maximum readability
- Creates clean, modern aesthetic

**Color Contrast**:
- Text on white: Minimum 4.5:1 ratio
- Text on orange: Use white text (21:1 ratio)
- Interactive elements: Clear visual feedback

### CSS Variables
```css
:root {
  --primary: 16 100% 50%;
  --primary-foreground: 0 0% 100%;
  --background: 0 0% 100%;
  --foreground: 0 0% 15%;
  --muted: 0 0% 96%;
  --border: 0 0% 90%;
}
```

---

## Typography

### Font Stack

**Display Font (Headers)**: **Poppins**
- Modern, geometric, friendly
- Weights: 400, 500, 600, 700, 800
- Used for: h1, h2, h3, h4, h5, h6
- Letter spacing: -0.02em to -0.03em (tighter for modern look)

**Body Font**: **Inter**
- Excellent screen readability
- Weights: 400, 500, 600, 700, 800
- Used for: Body text, UI elements, buttons
- Letter spacing: Normal

**Fallback Stack**:
```css
font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 
  'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

### Type Scale

**Desktop**:
- **H1**: 3rem (48px) / 700 / -0.03em
- **H2**: 2.25rem (36px) / 600 / -0.02em
- **H3**: 1.875rem (30px) / 600 / -0.02em
- **H4**: 1.5rem (24px) / 600 / -0.02em
- **Body**: 1rem (16px) / 400 / normal
- **Small**: 0.875rem (14px) / 400 / normal

**Mobile**:
- **H1**: 2rem (32px) / 700 / -0.03em
- **H2**: 1.75rem (28px) / 600 / -0.02em
- **H3**: 1.5rem (24px) / 600 / -0.02em
- **Body**: 1rem (16px) / 400 / normal

### Typography Guidelines

1. **Hierarchy**: Clear visual distinction between heading levels
2. **Readability**: Minimum 16px for body text, 1.5 line height
3. **Line Length**: 45-75 characters for optimal reading
4. **Contrast**: Minimum 4.5:1 for body text, 3:1 for large text
5. **Spacing**: Generous margins between sections

---

## Layout & Spacing

### Grid System

**Container Widths**:
- Mobile: Full width with 1rem padding
- Tablet: Max 768px, centered
- Desktop: Max 1280px, centered
- Large: Max 1400px, centered

**Grid Layouts**:
```css
/* Mobile: Single column */
.grid { grid-template-columns: 1fr; }

/* Tablet: 2 columns */
@media (min-width: 768px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
}

/* Desktop: 3 columns */
@media (min-width: 1024px) {
  .grid { grid-template-columns: repeat(3, 1fr); }
}
```

### Spacing Scale

Based on 4px base unit:
- **xs**: 0.25rem (4px)
- **sm**: 0.5rem (8px)
- **md**: 1rem (16px)
- **lg**: 1.5rem (24px)
- **xl**: 2rem (32px)
- **2xl**: 3rem (48px)
- **3xl**: 4rem (64px)

### White Space Principles

1. **Grouping**: Related elements close together (8-16px)
2. **Separation**: Unrelated sections separated (32-64px)
3. **Breathing Room**: Generous padding around content (24-48px)
4. **Visual Balance**: Asymmetric but balanced layouts

---

## Navigation

### Navigation Patterns

**Desktop Navigation**:
- Horizontal top navigation bar
- Logo on left, menu items center/right
- Dropdown menus for sub-items
- Search icon in header
- User menu (profile, settings)

**Mobile Navigation**:
- Bottom navigation bar (primary actions)
- Hamburger menu for secondary items
- Sticky header with back button
- Search accessible from header

### Navigation Best Practices

1. **Consistency**: Same navigation structure across all pages
2. **Clarity**: Clear labels, avoid abbreviations
3. **Feedback**: Active state clearly visible
4. **Accessibility**: Keyboard navigation, ARIA labels
5. **Performance**: Fast transitions, no jank

### Implementation Example
```tsx
// Mobile Bottom Navigation
const navItems = [
  { label: "Home", path: "/", icon: Home },
  { label: "Devotionals", path: "/feed", icon: BookOpen },
  { label: "Groups", path: "/groups", icon: Users },
  { label: "Profile", path: "/profile", icon: User },
];

// Active state styling
.active {
  color: hsl(var(--primary));
  background: hsl(var(--primary) / 0.1);
}
```

---

## Mobile Optimization

### Mobile-First Strategy

**Design Process**:
1. Design for 320px width first
2. Test on actual devices
3. Enhance for larger screens
4. Never degrade mobile experience

### Touch Targets

**Minimum Sizes**:
- **Buttons**: 44x44px minimum
- **Links**: 44px height minimum
- **Form Inputs**: 44px height minimum
- **Icon Buttons**: 48x48px recommended

**Spacing Between Targets**:
- Minimum 8px between interactive elements
- Prevents accidental taps

### Mobile-Specific Patterns

1. **Pull-to-Refresh**: For lists and feeds
2. **Swipe Gestures**: For cards and navigation
3. **Bottom Sheets**: For modals and forms
4. **Sticky Headers**: Navigation always accessible
5. **Infinite Scroll**: For long lists (with "Load More" option)

### Performance on Mobile

- **Image Optimization**: Serve appropriate sizes
- **Lazy Loading**: Load content as needed
- **Code Splitting**: Reduce initial bundle
- **Service Worker**: Offline support
- **Progressive Enhancement**: Works without JavaScript

---

## Animations & Interactions

### Animation Principles

1. **Purposeful**: Every animation serves a function
2. **Subtle**: Enhance, don't distract
3. **Fast**: 200-300ms for micro-interactions
4. **Smooth**: 60fps, use `transform` and `opacity`
5. **Respectful**: Honor `prefers-reduced-motion`

### Animation Types

**Micro-Interactions**:
- Button hover: Scale 1.02, 200ms
- Link hover: Color transition, 150ms
- Card hover: Shadow elevation, 200ms

**Page Transitions**:
- Fade in: 300ms ease-out
- Slide up: 400ms ease-out
- Stagger children: 50ms delay

**Loading States**:
- Skeleton loaders (preferred over spinners)
- Progress indicators for long operations
- Optimistic UI updates

### Implementation

```tsx
// Framer Motion Example
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3, ease: "easeOut" }}
>
  {content}
</motion.div>

// CSS Transitions
.button {
  transition: all 200ms ease;
}

.button:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
```

### Accessibility

```css
/* Respect user preferences */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Call-to-Actions (CTAs)

### CTA Hierarchy

**Primary CTA**:
- One per page/section
- Orange background, white text
- Prominent placement
- Action-oriented copy

**Secondary CTA**:
- Alternative actions
- Outline style, orange border
- Less prominent

**Tertiary CTA**:
- Text links
- Subtle styling
- For less important actions

### CTA Best Practices

1. **Clear Language**: "Join Us Sunday" not "Click Here"
2. **Visual Prominence**: Size, color, placement
3. **Context**: Relevant to page content
4. **Mobile**: Full-width buttons for easy tapping
5. **Feedback**: Loading states, success messages

### CTA Examples

```tsx
// Primary CTA
<Button className="bg-primary text-primary-foreground w-full md:w-auto px-8 py-3 text-lg font-semibold">
  Join Us This Sunday
</Button>

// Secondary CTA
<Button variant="outline" className="border-2 border-primary text-primary">
  Watch Online
</Button>

// Tertiary CTA
<Link className="text-primary hover:underline">
  Learn More
</Link>
```

---

## Performance

### Performance Budgets

**JavaScript**:
- Initial bundle: < 200KB gzipped
- Total bundle: < 500KB gzipped
- Code splitting required

**Images**:
- WebP format preferred
- Lazy loading for below-fold
- Responsive images with `srcset`
- Maximum 2MB per image (optimize to < 200KB)

**Fonts**:
- Subset fonts (only needed characters)
- Preload critical fonts
- Use `font-display: swap`
- Maximum 2 font families

### Optimization Checklist

- [ ] Code splitting implemented
- [ ] Images optimized (WebP, lazy loading)
- [ ] Fonts subsetted and preloaded
- [ ] Service worker caching
- [ ] Bundle size monitored
- [ ] Lighthouse score > 90

---

## Accessibility

### WCAG 2.1 AA Compliance

**Color Contrast**:
- Normal text: 4.5:1 minimum
- Large text: 3:1 minimum
- Interactive elements: 3:1 minimum

**Keyboard Navigation**:
- All interactive elements focusable
- Visible focus indicators
- Logical tab order
- Skip links for main content

**Screen Readers**:
- Semantic HTML
- ARIA labels where needed
- Alt text for images
- Form labels associated

**Implementation**:
```tsx
// Accessible Button
<button
  aria-label="Join group"
  className="focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
>
  Join Group
</button>

// Accessible Image
<img
  src="hero.jpg"
  alt="People worshiping together at church service"
  loading="lazy"
/>
```

---

## Component Patterns

### Card Component

**Structure**:
- Image (optional, top)
- Header (title, metadata)
- Content (description, text)
- Footer (actions, CTAs)

**Styling**:
- White background
- Subtle border or shadow
- Rounded corners (12px)
- Hover elevation

```tsx
<Card className="bg-white rounded-xl border border-border hover:shadow-lg transition-shadow">
  <CardHeader>
    <CardTitle>Group Name</CardTitle>
    <CardDescription>Description text</CardDescription>
  </CardHeader>
  <CardContent>
    {content}
  </CardContent>
  <CardFooter>
    <Button>Join Group</Button>
  </CardFooter>
</Card>
```

### Form Patterns

**Input Fields**:
- Clear labels above inputs
- Placeholder text for guidance
- Error states clearly visible
- Success feedback

**Mobile Forms**:
- Full-width inputs
- Large touch targets
- Native inputs when possible
- Clear submit buttons

---

## Implementation Checklist

### Design Phase
- [ ] User research and personas defined
- [ ] User flows mapped
- [ ] Wireframes created (mobile-first)
- [ ] Design system documented
- [ ] Accessibility requirements defined

### Development Phase
- [ ] Mobile-first CSS written
- [ ] Components built with accessibility
- [ ] Performance budgets met
- [ ] Cross-browser testing
- [ ] Device testing (iOS, Android)

### Quality Assurance
- [ ] Lighthouse audit > 90
- [ ] Accessibility audit passed
- [ ] Performance targets met
- [ ] User testing completed
- [ ] Analytics implemented

---

## Common Mistakes to Avoid

Based on [Tithely's analysis](https://get.tithe.ly/blog/5-examples-of-great-church-websites-and-why-we-think-theyre-awesome):

1. **Cluttered Layouts**: Too much information, no hierarchy
2. **Confusing Navigation**: Unclear labels, too many menu items
3. **Missing CTAs**: No clear next steps for users
4. **Slow Loading**: Unoptimized images, large bundles
5. **Poor Mobile Experience**: Desktop-only design
6. **Inaccessible Design**: Poor contrast, no keyboard navigation
7. **Outdated Aesthetics**: Looks dated, doesn't inspire

---

## Resources

### Design Tools
- **Figma**: Design and prototyping
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Component library
- **Framer Motion**: Animation library

### Testing Tools
- **Lighthouse**: Performance and accessibility
- **WebPageTest**: Performance analysis
- **axe DevTools**: Accessibility testing
- **BrowserStack**: Cross-browser testing

### Inspiration
- [North Point Community Church](https://northpoint.org/)
- [Deeper/Wider Initiative](https://deeperwider.com/)
- [Tithely Best Practices](https://get.tithe.ly/blog/5-examples-of-great-church-websites-and-why-we-think-theyre-awesome)

---

## Conclusion

This design guide serves as the foundation for all KasaAI applications. By following these principles, we ensure:

- **Consistent** user experiences across all apps
- **Engaging** interfaces that inspire action
- **Accessible** designs that include everyone
- **Performant** applications that load quickly
- **Modern** aesthetics that build trust

**Remember**: Great design is invisible. Users should feel the impact, not see the effort.

---

**Last Updated**: 2024-12-19  
**Next Review**: 2025-03-19

