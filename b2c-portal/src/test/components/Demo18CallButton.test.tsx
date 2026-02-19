import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Demo18CallButton from "../../components/Demo18CallButton";

describe("Demo18CallButton", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("connects successfully", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: true } as Response);
    render(<Demo18CallButton />);
    fireEvent.click(screen.getByText(/Start Session/i));
    await screen.findByText(/Connected/i);
    expect(screen.getByText(/Start Session/i)).toBeDisabled();
  });

  it("shows error on failure", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({ ok: false } as Response);
    render(<Demo18CallButton />);
    fireEvent.click(screen.getByText(/Start Session/i));
    await screen.findByText(/Error/i);
  });

  it("disables stop button when idle", () => {
    render(<Demo18CallButton />);
    expect(screen.getByText(/Stop Session/i)).toBeDisabled();
  });
});
