/**
 * EstateFlow Campaigns Page
 *
 * Uses centralized campaign components from @shared/frontend/campaigns
 */

import { useState } from "react";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { CampaignList } from "@/components/shared/CampaignList";
import { CampaignAnalytics } from "@/components/shared/CampaignAnalytics";
import { ContactList } from "@/components/shared/ContactList";
import type { Campaign } from "@/components/shared/CampaignList";
import type { Contact } from "@/components/shared/ContactList";
import { CampaignWizard } from "@/components/CampaignWizard";
import { ContactFormDialog, ContactFormData } from "@/components/ContactFormDialog";

const API_BASE_URL = import.meta.env.VITE_API_URL || "https://estateflow-api.ailabsafrica.com";

export default function Campaigns() {
  const [activeTab, setActiveTab] = useState<"campaigns" | "contacts">("campaigns");
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [contactFormOpen, setContactFormOpen] = useState(false);

  // Get auth token from localStorage
  const token = localStorage.getItem("access_token") || "";

  const handleCreateContact = async (data: ContactFormData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/campaigns/contacts`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...data,
          custom_data: {
            property_type_preferences: data.property_type_preferences,
            location_preferences: data.location_preferences,
            budget_min: data.budget_min,
            budget_max: data.budget_max,
          },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create contact");
      }

      // Refresh the contact list
      window.location.reload();
    } catch (error) {
      console.error("Error creating contact:", error);
      throw error;
    }
  };

  return (
    <div className="min-h-screen">
      <Header
        title="Campaigns"
        subtitle="Manage your multi-channel marketing campaigns"
        actions={
          activeTab === "campaigns" ? (
            <Button variant="gradient" className="gap-2" onClick={() => setWizardOpen(true)}>
              <Plus className="h-4 w-4" />
              New Campaign
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button variant="gradient" className="gap-2" onClick={() => setContactFormOpen(true)}>
                <Plus className="h-4 w-4" />
                Add Contact
              </Button>
            </div>
          )
        }
      />

      {/* Campaign Creation Wizard */}
      <CampaignWizard open={wizardOpen} onClose={() => setWizardOpen(false)} />

      {/* Contact Form Dialog */}
      <ContactFormDialog
        open={contactFormOpen}
        onClose={() => {
          setContactFormOpen(false);
          setSelectedContact(null);
        }}
        contact={selectedContact}
        onSubmit={handleCreateContact}
      />

      <div className="p-6">
        {/* Tabs */}
        <div className="border-b border-border mb-6 animate-slide-up-fade">
          <nav className="-mb-px flex gap-6">
            <button
              onClick={() => setActiveTab("campaigns")}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-all duration-200 ${
                activeTab === "campaigns"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-primary/30"
              }`}
            >
              Campaigns
            </button>
            <button
              onClick={() => setActiveTab("contacts")}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-all duration-200 ${
                activeTab === "contacts"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-primary/30"
              }`}
            >
              Contacts
            </button>
          </nav>
        </div>

        {/* Content */}
        {activeTab === "campaigns" ? (
          <CampaignList
            apiBaseUrl={API_BASE_URL}
            authToken={token}
            onCampaignClick={(campaign) => {
              setSelectedCampaign(campaign);
              setShowAnalytics(true);
            }}
            onLaunch={(id) => {
              console.log("Campaign launched:", id);
            }}
            onCreateNew={() => {
              setWizardOpen(true);
            }}
          />
        ) : (
          <ContactList
            apiBaseUrl={API_BASE_URL}
            authToken={token}
            onContactClick={(contact) => {
              setSelectedContact(contact);
              setContactFormOpen(true);
            }}
            onCreateNew={() => {
              setContactFormOpen(true);
            }}
            onImportSuccess={() => {
              console.log("Import successful!");
              window.location.reload();
            }}
          />
        )}

        {/* Analytics Modal */}
        {selectedCampaign && (
          <CampaignAnalytics
            campaignId={selectedCampaign.id}
            apiBaseUrl={API_BASE_URL}
            authToken={token}
            isOpen={showAnalytics}
            onClose={() => {
              setShowAnalytics(false);
              setSelectedCampaign(null);
            }}
          />
        )}
      </div>
    </div>
  );
}
