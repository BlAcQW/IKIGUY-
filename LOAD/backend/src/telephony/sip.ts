/**
 * SIP trunking support.
 * Future implementation.
 */

export interface SIPConfig {
  endpoint: string;
  username: string;
  password: string;
}

export function createSIPClient(_config: SIPConfig) {
  throw new Error('SIP integration not yet implemented');
}
