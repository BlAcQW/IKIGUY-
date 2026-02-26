import Vapi from '@vapi-ai/web';
import type { Call } from '@vapi-ai/web/dist/api';

const VAPI_PUBLIC_KEY = import.meta.env.VITE_VAPI_PUBLIC_KEY;
const ASSISTANT_ID = 'dabccfdc-f6d5-45dc-9699-c8aed7a15058';

let vapiInstance: Vapi | null = null;

function getVapiInstance(): Vapi {
  if (!vapiInstance) {
    if (!VAPI_PUBLIC_KEY) {
      throw new Error('VITE_VAPI_PUBLIC_KEY is not set');
    }
    vapiInstance = new Vapi(VAPI_PUBLIC_KEY);
  }
  return vapiInstance;
}

export async function startCall(): Promise<Call | null> {
  const vapi = getVapiInstance();
  return vapi.start(ASSISTANT_ID);
}

export async function stopCall(): Promise<void> {
  const vapi = getVapiInstance();
  await vapi.stop();
}

export function removeAllListeners(): void {
  if (vapiInstance) {
    vapiInstance.removeAllListeners();
  }
}

export function toggleMute(): boolean {
  const vapi = getVapiInstance();
  const muted = vapi.isMuted();
  vapi.setMuted(!muted);
  return !muted;
}

export function isMuted(): boolean {
  const vapi = getVapiInstance();
  return vapi.isMuted();
}

export { getVapiInstance };
