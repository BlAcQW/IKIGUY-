/**
 * TimePicker Component Tests
 *
 * Tests the enhanced time picker component functionality
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TimePicker from '../TimePicker'

describe('TimePicker', () => {
  it('renders with label and initial value', () => {
    const onChange = vi.fn()
    render(
      <TimePicker
        value="09:00"
        onChange={onChange}
        label="Start Time"
      />
    )

    expect(screen.getByText('Start Time')).toBeInTheDocument()
    expect(screen.getByText('9:00 AM')).toBeInTheDocument()
  })

  it('shows required asterisk when required prop is true', () => {
    const onChange = vi.fn()
    render(
      <TimePicker
        value="09:00"
        onChange={onChange}
        label="Start Time"
        required
      />
    )

    expect(screen.getByText('*')).toBeInTheDocument()
  })

  it('opens dropdown when clicked', () => {
    const onChange = vi.fn()
    render(
      <TimePicker
        value="09:00"
        onChange={onChange}
        label="Start Time"
      />
    )

    const display = screen.getByText('9:00 AM')
    fireEvent.click(display)

    expect(screen.getByText('Quick Select')).toBeInTheDocument()
  })

  it('calls onChange when preset time is selected', () => {
    const onChange = vi.fn()
    render(
      <TimePicker
        value="09:00"
        onChange={onChange}
        label="Start Time"
      />
    )

    // Open dropdown
    const display = screen.getByText('9:00 AM')
    fireEvent.click(display)

    // Click on 2:00 PM preset
    const preset = screen.getByText('2:00 PM')
    fireEvent.click(preset)

    expect(onChange).toHaveBeenCalledWith('14:00')
  })

  it('filters presets based on maxTime constraint', () => {
    const onChange = vi.fn()
    render(
      <TimePicker
        value="09:00"
        onChange={onChange}
        label="Start Time"
        maxTime="12:00"
      />
    )

    // Open dropdown
    const display = screen.getByText('9:00 AM')
    fireEvent.click(display)

    // Should show times up to 12:00 PM
    expect(screen.getByText('11:00 AM')).toBeInTheDocument()
    expect(screen.getByText('12:00 PM')).toBeInTheDocument()

    // Should NOT show times after 12:00 PM
    expect(screen.queryByText('1:00 PM')).not.toBeInTheDocument()
    expect(screen.queryByText('2:00 PM')).not.toBeInTheDocument()
  })

  it('filters presets based on minTime constraint', () => {
    const onChange = vi.fn()
    render(
      <TimePicker
        value="14:00"
        onChange={onChange}
        label="End Time"
        minTime="10:00"
      />
    )

    // Open dropdown
    const display = screen.getByText('2:00 PM')
    fireEvent.click(display)

    // Should show times from 10:00 AM onwards
    expect(screen.getByText('10:00 AM')).toBeInTheDocument()
    expect(screen.getByText('2:00 PM')).toBeInTheDocument()

    // Should NOT show times before 10:00 AM
    expect(screen.queryByText('6:00 AM')).not.toBeInTheDocument()
    expect(screen.queryByText('9:00 AM')).not.toBeInTheDocument()
  })

  it('displays time in 24-hour format when toggled', () => {
    const onChange = vi.fn()
    render(
      <TimePicker
        value="14:00"
        onChange={onChange}
        label="Time"
      />
    )

    // Initially shows 12-hour format
    expect(screen.getByText('2:00 PM')).toBeInTheDocument()

    // Open dropdown
    fireEvent.click(screen.getByText('2:00 PM'))

    // Toggle to 24-hour format
    const toggle24h = screen.getByText('24h')
    fireEvent.click(toggle24h)

    // Should now show 24-hour format
    expect(screen.getByText('14:00')).toBeInTheDocument()
  })

  it('is disabled when disabled prop is true', () => {
    const onChange = vi.fn()
    const { container } = render(
      <TimePicker
        value="09:00"
        onChange={onChange}
        label="Start Time"
        disabled
      />
    )

    const display = container.querySelector('.cursor-not-allowed')
    expect(display).toBeInTheDocument()

    // Clicking should not open dropdown
    fireEvent.click(display!)
    expect(screen.queryByText('Quick Select')).not.toBeInTheDocument()
  })

  it('shows validation message when value exceeds maxTime', () => {
    const onChange = vi.fn()
    render(
      <TimePicker
        value="15:00"
        onChange={onChange}
        label="End Time"
        maxTime="12:00"
      />
    )

    expect(screen.getByText(/must be at or before/i)).toBeInTheDocument()
  })

  it('shows validation message when value is before minTime', () => {
    const onChange = vi.fn()
    render(
      <TimePicker
        value="08:00"
        onChange={onChange}
        label="Start Time"
        minTime="10:00"
      />
    )

    expect(screen.getByText(/must be at or after/i)).toBeInTheDocument()
  })
})
