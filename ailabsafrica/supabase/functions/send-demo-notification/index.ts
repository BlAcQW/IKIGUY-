import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { Resend } from "npm:resend@2.0.0";

const resend = new Resend(Deno.env.get("RESEND_API_KEY"));

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface DemoNotificationRequest {
  fullName: string;
  companyName?: string;
  email: string;
  phone?: string;
  preferredDate: string;
  preferredTime: string;
  timezone: string;
  demoType: string;
  notes?: string;
}

const handler = async (req: Request): Promise<Response> => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const {
      fullName,
      companyName,
      email,
      phone,
      preferredDate,
      preferredTime,
      timezone,
      demoType,
      notes
    }: DemoNotificationRequest = await req.json();

    // Send notification email to alfred.anyan@gmail.com
    const notificationResponse = await resend.emails.send({
      from: "KasaAI Demo <onboarding@resend.dev>",
      to: ["alfred.anyan@gmail.com"],
      subject: `New Demo Request from ${fullName}`,
      html: `
        <h1>New Demo Booking Request</h1>
        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; font-family: Arial, sans-serif;">
          <h2>Contact Information</h2>
          <p><strong>Name:</strong> ${fullName}</p>
          <p><strong>Email:</strong> ${email}</p>
          ${companyName ? `<p><strong>Company:</strong> ${companyName}</p>` : ''}
          ${phone ? `<p><strong>Phone:</strong> ${phone}</p>` : ''}
          
          <h2>Demo Details</h2>
          <p><strong>Preferred Date:</strong> ${preferredDate}</p>
          <p><strong>Preferred Time:</strong> ${preferredTime}</p>
          <p><strong>Timezone:</strong> ${timezone}</p>
          <p><strong>Demo Type:</strong> ${demoType}</p>
          
          ${notes ? `
            <h2>Additional Notes</h2>
            <p>${notes}</p>
          ` : ''}
        </div>
      `,
    });

    // Send confirmation email to the customer
    const confirmationResponse = await resend.emails.send({
      from: "KasaAI <onboarding@resend.dev>",
      to: [email],
      subject: "Demo Request Received - KasaAI",
      html: `
        <h1>Thank you for your demo request, ${fullName}!</h1>
        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; font-family: Arial, sans-serif;">
          <p>We have received your demo request and will contact you soon to confirm your appointment.</p>
          
          <h2>Your Request Details</h2>
          <p><strong>Preferred Date:</strong> ${preferredDate}</p>
          <p><strong>Preferred Time:</strong> ${preferredTime}</p>
          <p><strong>Timezone:</strong> ${timezone}</p>
          <p><strong>Demo Type:</strong> ${demoType}</p>
          
          <p>If you have any questions, please don't hesitate to contact us.</p>
          
          <p>Best regards,<br>The KasaAI Team</p>
        </div>
      `,
    });

    console.log("Emails sent successfully:", { notificationResponse, confirmationResponse });

    return new Response(JSON.stringify({ 
      success: true,
      notificationSent: notificationResponse.data?.id ? true : false,
      confirmationSent: confirmationResponse.data?.id ? true : false
    }), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        ...corsHeaders,
      },
    });
  } catch (error: any) {
    console.error("Error in send-demo-notification function:", error);
    return new Response(
      JSON.stringify({ 
        error: error.message,
        success: false 
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      }
    );
  }
};

serve(handler);