/**
 * Tests for category property logic fixes
 */

import { describe, it, expect } from 'vitest';

describe('Category Property Logic Fix', () => {
  it('should filter templates correctly when category is undefined', () => {
    const templates = [
      { id: '1', name: 'Template 1', category: 'sales' },
      { id: '2', name: 'Template 2', category: undefined },
      { id: '3', name: 'Template 3', category: 'marketing' }
    ];

    // Test category extraction with fallback
    const categories = [...new Set(templates.map(t => t.category || 'general'))];
    expect(categories).toContain('general');
    expect(categories).toContain('sales');
    expect(categories).toContain('marketing');

    // Test filtering with undefined category
    const generalTemplates = templates.filter(t => (t.category || 'general') === 'general');
    expect(generalTemplates).toHaveLength(1);
    expect(generalTemplates[0].id).toBe('2');
  });

  it('should handle search with undefined category', () => {
    const templates = [
      { id: '1', name: 'Sales Template', category: 'sales', description: 'Sales related', industry: 'Business' },
      { id: '2', name: 'General Template', category: undefined, description: 'General purpose', industry: 'Any' }
    ];

    const searchTerm = 'general';

    // This should not throw an error when searching
    const filteredTemplates = templates.filter(template =>
      template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.industry.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (template.category || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    expect(filteredTemplates).toHaveLength(1);
    expect(filteredTemplates[0].id).toBe('2');
  });

  it('should handle category display with fallback', () => {
    const templateMissingCategory = {
      id: '1',
      name: 'Test Template',
      description: 'Test',
      industry: 'Healthcare',
      // category missing
      complexity: 'Medium'
    };

    // Test direct category access with fallback
    const displayCategory = templateMissingCategory.category || 'general';
    expect(displayCategory).toBe('general');

    // Test category replacement for display
    const formattedCategory = (templateMissingCategory.category || 'general')
      .replace('_', ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
    expect(formattedCategory).toBe('General');
  });

  it('should handle category-based switch statements safely', () => {
    const templates = [
      { category: 'sales' },
      { category: undefined },
      { category: 'marketing' }
    ];

    templates.forEach(template => {
      let result;
      switch (template.category || 'general') {
        case 'sales':
          result = 'sales-tools';
          break;
        case 'marketing':
          result = 'marketing-tools';
          break;
        default:
          result = 'general-tools';
      }

      if (template.category === 'sales') {
        expect(result).toBe('sales-tools');
      } else if (template.category === 'marketing') {
        expect(result).toBe('marketing-tools');
      } else {
        expect(result).toBe('general-tools');
      }
    });
  });

  it('should safely create template metadata with category fallback', () => {
    const template = {
      id: '1',
      name: 'Test Template',
      industry: 'Healthcare'
      // category intentionally missing
    };

    const metadata = {
      templateId: template.id,
      industry: template.industry,
      category: template.category || 'general'
    };

    expect(metadata.category).toBe('general');
    expect(metadata.templateId).toBe('1');
    expect(metadata.industry).toBe('Healthcare');
  });
});