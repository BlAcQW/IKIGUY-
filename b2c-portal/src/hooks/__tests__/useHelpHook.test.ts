import { renderHook, act } from '@testing-library/react';
import { useHelp } from '../useHelp';

describe('useHelp hook', () => {
  it('retrieves help content successfully', () => {
    const { result } = renderHook(() => useHelp());
    const content = result.current.getHelp('dashboard_overview');
    expect(content?.title).toBe('Dashboard Overview');
  });

  it('returns null for unknown key', () => {
    const { result } = renderHook(() => useHelp());
    expect(result.current.getHelp('unknown_key')).toBeNull();
  });

  it('does not open modal for invalid key', () => {
    const { result } = renderHook(() => useHelp());
    act(() => { result.current.openHelpModal('invalid'); });
    expect(result.current.isHelpModalOpen).toBe(false);
  });
});
