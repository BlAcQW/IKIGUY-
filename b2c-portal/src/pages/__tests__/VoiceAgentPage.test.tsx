import { render, screen, fireEvent } from "@/test/utils/test-utils";
import { describe, it, expect, vi } from "vitest";
import VoiceAgent from "@/pages/VoiceAgent";

const options = {
  stt: { openai: ["gpt-4o-transcribe"] },
  tts: { coqui: ["akuapem_female"] },
  llm: ["gpt-4o-mini"],
  languages: ["English"],
  countries: ["Ghana"],
};

describe("VoiceAgent configuration", () => {
  it("creates agent with selected options", async () => {
    vi.spyOn(global, "fetch" as any).mockResolvedValue({
      json: async () => options,
    } as Response);

    render(<VoiceAgent />);
    await screen.findByLabelText(/STT Provider/i);
    fireEvent.click(screen.getByText("Create Assistant"));
    await screen.findByText(/"sttProvider"/i);
    (global.fetch as any).mockRestore();
  });
});

describe("VoiceAgent loop", () => {
  it("loops audio and displays transcript", async () => {
    const fetchMock = vi.spyOn(global, "fetch" as any);
    fetchMock.mockResolvedValueOnce({ json: async () => options } as Response);
    for (let i = 0; i < 6; i++) {
      fetchMock.mockResolvedValueOnce({ json: async () => ({ voice: false }) } as Response);
    }
    fetchMock.mockResolvedValueOnce({
      json: async () => ({ partials: ["hi"], text: "hi", samples: [1, 2] }),
    } as Response);

    (global as any).AudioContext = class {
      sampleRate = 48000;
      createBuffer() {
        return { getChannelData: () => new Float32Array(2) };
      }
      createBufferSource() {
        return { connect: () => undefined, start: () => undefined, buffer: null };
      }
      createMediaStreamSource() {
        return { connect: () => undefined, disconnect: () => undefined };
      }
      createScriptProcessor() {
        const proc: any = {
          connect: () => undefined,
          disconnect: () => undefined,
          onaudioprocess: null,
        };
        setTimeout(() => {
          const buffer = { getChannelData: () => new Float32Array(1024) } as any;
          for (let i = 0; i < 6; i++) {
            proc.onaudioprocess?.({ inputBuffer: buffer });
          }
        }, 0);
        return proc;
      }
      destination = {};
    };
    navigator.mediaDevices = {
      getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [{ stop: () => undefined }] }),
    } as any;

    render(<VoiceAgent />);
    const btn = await screen.findByText("Talk to Assistant");
    fireEvent.click(btn);
    await screen.findByText(/User: hi/);
    fetchMock.mockRestore();
  });
});

describe("VoiceAgent conversation", () => {
  it("processes user speech and speaks LLM reply", async () => {
    const fetchMock = vi.spyOn(global, "fetch" as any);
    fetchMock.mockResolvedValueOnce({ json: async () => options } as Response);
    for (let i = 0; i < 6; i++) {
      fetchMock.mockResolvedValueOnce({ json: async () => ({ voice: false }) } as Response);
    }
    fetchMock.mockResolvedValueOnce({
      json: async () => ({ partials: ["hi"], text: "hi" }),
    } as Response);
    fetchMock.mockResolvedValueOnce({ json: async () => ({ reply: "hey" }) } as Response);
    fetchMock.mockResolvedValueOnce({ json: async () => ({ samples: [1, 2] }) } as Response);

    (global as any).AudioContext = class {
      sampleRate = 48000;
      createBuffer() {
        return { getChannelData: () => new Float32Array(2) };
      }
      createBufferSource() {
        return { connect: () => undefined, start: () => undefined, buffer: null };
      }
      createMediaStreamSource() {
        return { connect: () => undefined, disconnect: () => undefined };
      }
      createScriptProcessor() {
        const proc: any = {
          connect: () => undefined,
          disconnect: () => undefined,
          onaudioprocess: null,
        };
        setTimeout(() => {
          const buffer = { getChannelData: () => new Float32Array(1024) } as any;
          for (let i = 0; i < 6; i++) {
            proc.onaudioprocess?.({ inputBuffer: buffer });
          }
        }, 0);
        return proc;
      }
      destination = {};
    };
    navigator.mediaDevices = {
      getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [{ stop: () => undefined }] }),
    } as any;

    render(<VoiceAgent />);
    const btn = await screen.findByText("Talk to Assistant");
    fireEvent.click(btn);
    await screen.findByText(/Assistant: hey/);
    fetchMock.mockRestore();
  });
});
