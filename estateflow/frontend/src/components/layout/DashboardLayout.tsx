import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { MobileHeader } from "./MobileHeader";
import { useIsMobile } from "@/hooks/use-mobile";

export function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isMobile = useIsMobile();

  return (
    <div className="min-h-screen bg-background">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        isMobile={isMobile}
      />
      <main className={isMobile ? "" : "lg:pl-64"}>
        {isMobile && <MobileHeader onMenuClick={() => setSidebarOpen(true)} />}
        <Outlet />
      </main>
    </div>
  );
}
