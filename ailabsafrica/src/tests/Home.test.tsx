import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect } from 'vitest';
import Home from '@/pages/Home';

// Mock the ImageOptimizer components
vi.mock('@/components/ImageOptimizer', () => ({
  ImageOptimizer: ({ alt, ...props }: any) => <img alt={alt} {...props} />,
  BackgroundImage: ({ children, alt, ...props }: any) => (
    <div data-testid="background-image" {...props}>
      {children}
    </div>
  ),
}));

// Mock the image assets
vi.mock('@/assets/hero-bg.jpg', () => ({ default: 'hero-bg.jpg' }));
vi.mock('@/assets/kasaai-product.jpg', () => ({ default: 'kasaai-product.jpg' }));

const renderHome = () => {
  return render(
    <BrowserRouter>
      <Home />
    </BrowserRouter>
  );
};

describe('Home Page', () => {
  describe('Hero Section', () => {
    it('renders hero section with main heading', () => {
      renderHome();
      
      expect(screen.getByText('AI Labs Africa')).toBeInTheDocument();
    });

    it('renders hero description', () => {
      renderHome();
      
      expect(screen.getByText(/Pioneering AI innovation across Africa/)).toBeInTheDocument();
    });

    it('renders call-to-action buttons', () => {
      renderHome();
      
      const exploreDemosLinks = screen.getAllByRole('link', { name: /Explore Demos/i });
      const getStartedLinks = screen.getAllByRole('link', { name: /Get Started/i });
      
      expect(exploreDemosLinks.length).toBeGreaterThan(0);
      expect(getStartedLinks.length).toBeGreaterThan(0);
    });

    it('has correct links for CTA buttons', () => {
      renderHome();
      
      const exploreDemosLinks = screen.getAllByRole('link', { name: /Explore Demos/i });
      const getStartedLinks = screen.getAllByRole('link', { name: /Get Started/i });
      
      exploreDemosLinks.forEach(link => {
        expect(link).toHaveAttribute('href', '/demos');
      });
      
      getStartedLinks.forEach(link => {
        expect(link).toHaveAttribute('href', '/contact');
      });
    });
  });

  describe('About Section', () => {
    it('renders about section heading', () => {
      renderHome();
      
      expect(screen.getByText(/Transforming Africa with AI Innovation/)).toBeInTheDocument();
    });

    it('renders about section content', () => {
      renderHome();
      
      expect(screen.getByText(/We're building the future of artificial intelligence in Africa/)).toBeInTheDocument();
    });

    it('renders feature cards', () => {
      renderHome();
      
      expect(screen.getByText('AI-First Approach')).toBeInTheDocument();
      expect(screen.getByText('Local Innovation')).toBeInTheDocument();
      expect(screen.getByText('Scalable Impact')).toBeInTheDocument();
    });
  });

  describe('Product Showcase', () => {
    it('renders product showcase section', () => {
      renderHome();
      
      expect(screen.getByText(/Meet KasaAI/)).toBeInTheDocument();
    });

    it('renders product features', () => {
      renderHome();
      
      expect(screen.getByText(/Multi-channel Support/)).toBeInTheDocument();
      expect(screen.getByText(/Voice Automation/)).toBeInTheDocument();
      expect(screen.getByText(/Multiple Languages/)).toBeInTheDocument();
      expect(screen.getByText(/Enterprise Security/)).toBeInTheDocument();
    });

    it('renders demo buttons', () => {
      renderHome();
      
      expect(screen.getByRole('link', { name: /Try Live Demos/i })).toBeInTheDocument();
      const scheduleDemoLinks = screen.getAllByRole('link', { name: /Schedule Demo/i });
      expect(scheduleDemoLinks.length).toBeGreaterThan(0);
    });
  });

  describe('Industries Section', () => {
    it('renders industries section heading', () => {
      renderHome();
      
      expect(screen.getByText(/Industries We Serve/)).toBeInTheDocument();
    });

    it('renders industry cards', () => {
      renderHome();
      
      expect(screen.getByText(/Insurance/)).toBeInTheDocument();
      expect(screen.getByText(/Banking & Finance/)).toBeInTheDocument();
      expect(screen.getByText(/Real Estate/)).toBeInTheDocument();
      expect(screen.getByText(/Retail & E-commerce/)).toBeInTheDocument();
      expect(screen.getByText(/Healthcare/)).toBeInTheDocument();
      expect(screen.getByText(/Government Services/)).toBeInTheDocument();
    });
  });

  describe('Call to Action Section', () => {
    it('renders final call to action', () => {
      renderHome();
      
      expect(screen.getByText(/Ready to Transform Your Business?/)).toBeInTheDocument();
    });

    it('renders CTA description', () => {
      renderHome();
      
      expect(screen.getByText(/Join the AI revolution in Africa/)).toBeInTheDocument();
    });

    it('renders CTA buttons', () => {
      renderHome();
      
      const exploreDemosLinks = screen.getAllByRole('link', { name: /Explore Demos/i });
      const scheduleDemoLinks = screen.getAllByRole('link', { name: /Schedule Demo/i });
      
      expect(exploreDemosLinks.length).toBeGreaterThan(0);
      expect(scheduleDemoLinks.length).toBeGreaterThan(0);
    });
  });

  describe('Navigation Links', () => {
    it('has correct link to demos page', () => {
      renderHome();
      
      const demosLinks = screen.getAllByText(/Explore Demos|Try Live Demos/);
      demosLinks.forEach(link => {
        expect(link.closest('a')).toHaveAttribute('href', '/demos');
      });
    });

    it('has correct link to contact page', () => {
      renderHome();
      
      const contactLink = screen.getByText('Get Started');
      expect(contactLink.closest('a')).toHaveAttribute('href', '/contact');
    });

    it('has correct link to schedule demo page', () => {
      renderHome();
      
      const scheduleDemoLinks = screen.getAllByText('Schedule Demo');
      scheduleDemoLinks.forEach(link => {
        expect(link.closest('a')).toHaveAttribute('href', '/schedule-demo');
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      renderHome();
      
      const headings = screen.getAllByRole('heading');
      expect(headings.length).toBeGreaterThan(0);
      
      // Check for main heading
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });

    it('has proper link structure', () => {
      renderHome();
      
      const links = screen.getAllByRole('link');
      expect(links.length).toBeGreaterThan(0);
      
      // All links should have href attributes
      links.forEach(link => {
        expect(link).toHaveAttribute('href');
      });
    });

    it('has proper link structure', () => {
      renderHome();
      
      const links = screen.getAllByRole('link');
      expect(links.length).toBeGreaterThan(0);
      
      // All links should have href attributes
      links.forEach(link => {
        expect(link).toHaveAttribute('href');
      });
    });
  });

  describe('Layout and Styling', () => {
    it('renders without crashing', () => {
      expect(() => renderHome()).not.toThrow();
    });

    it('renders all main sections', () => {
      renderHome();
      
      // Check that all main sections are present
      expect(screen.getByText('AI Labs Africa')).toBeInTheDocument();
      expect(screen.getByText(/Transforming Africa with AI Innovation/)).toBeInTheDocument();
      expect(screen.getByText(/Meet KasaAI/)).toBeInTheDocument();
      expect(screen.getByText(/Industries We Serve/)).toBeInTheDocument();
      expect(screen.getByText(/Ready to Transform Your Business?/)).toBeInTheDocument();
    });
  });
});
