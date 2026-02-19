import { GoogleGenerativeAI } from '@google/generative-ai';

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(import.meta.env.GEMINI_API_KEY || '');

export interface SummaryRequest {
  transcript: string;
  callId: string;
  assistantName?: string;
  callDuration?: number;
}

export interface SummaryResponse {
  summary: string;
  keyPoints: string[];
  sentiment: 'positive' | 'neutral' | 'negative';
  actionItems: string[];
}

export const generateCallSummary = async (request: SummaryRequest): Promise<SummaryResponse> => {
  try {
    // Check if API key is available
    if (!import.meta.env.GEMINI_API_KEY) {
      throw new Error('Gemini API key not configured');
    }
    
    const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });

    const prompt = `
You are an AI assistant that analyzes call transcripts and provides concise, professional summaries.

Call Details:
- Assistant: ${request.assistantName || 'Voice Assistant'}
- Duration: ${request.callDuration ? `${request.callDuration} minutes` : 'Unknown'}
- Call ID: ${request.callId}

Please analyze the following transcript and provide:

1. A concise summary (2-3 sentences) of the conversation
2. Key points discussed (3-5 bullet points)
3. Overall sentiment (positive, neutral, or negative)
4. Any action items or follow-ups needed (if any)

Transcript:
${request.transcript}

Please respond in the following JSON format:
{
  "summary": "Brief summary of the conversation",
  "keyPoints": ["Point 1", "Point 2", "Point 3"],
  "sentiment": "positive|neutral|negative",
  "actionItems": ["Action 1", "Action 2"]
}
`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text();
    
    // Try to parse JSON response
    try {
      const parsed = JSON.parse(text);
      return {
        summary: parsed.summary || 'Summary generated successfully.',
        keyPoints: parsed.keyPoints || [],
        sentiment: parsed.sentiment || 'neutral',
        actionItems: parsed.actionItems || []
      };
    } catch (parseError) {
      // Fallback if JSON parsing fails
      return {
        summary: text || 'Summary generated successfully.',
        keyPoints: [],
        sentiment: 'neutral',
        actionItems: []
      };
    }
  } catch (error) {
    console.error('Error generating summary with Gemini:', error);
    throw new Error('Failed to generate summary');
  }
};

export const generateQuickSummary = async (transcript: string): Promise<string> => {
  try {
    const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });

    const prompt = `
Please provide a brief, professional summary of this call transcript in 2-3 sentences:

${transcript}

Summary:`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    return response.text().trim();
  } catch (error) {
    console.error('Error generating quick summary:', error);
    throw new Error('Failed to generate summary');
  }
};
