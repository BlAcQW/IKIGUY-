# Inbound PSTN Provider Options

The table below summarizes options for handling inbound public switched telephone network (PSTN) calls for Demo 19.

| Provider | Ghana number availability | Approx inbound cost/min* | Webhook → WebSocket bridge | DTMF support | Consent recording |
|----------|--------------------------|---------------------------|-----------------------------|--------------|-------------------|
| **VAPI** | Bring-your-own number; can sit on top of Twilio/Vonage | ~USD 0.02 (carrier dependent) | Native WebSocket session from webhook | ✅ via VAPI events | Built-in recording controls |
| **Twilio** | No local Ghana numbers; requires international or SIP trunks | ~USD 0.013 (US DID) + international forwarding | Use `<Stream>` API to forward audio to WebSocket bridge | ✅ via TwiML `<Gather>` | Call recording API |
| **Vonage** | Limited—contact sales for Ghana numbers | ~USD 0.015 (varies) | Voice API supports WebSocket for audio streaming | ✅ via Input event | Call recording API |

\*Costs are rough 2024 rates and depend on the underlying carrier and number type.

**Considerations**

- **Coverage:** VAPI rides on existing carriers; Twilio lacks native Ghana numbers; Vonage availability is unclear.
- **Bridging:** All support webhooks that can proxy audio to the voice engine WebSocket.
- **DTMF:** Each exposes keypad events for IVR flows.
- **Consent:** Twilio and Vonage expose recording APIs; VAPI can gate consent before recording.
