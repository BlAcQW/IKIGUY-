import { Outlet } from "react-router-dom";
import { PublicHeader } from "./PublicHeader";
import { Footer } from "./Footer";
import { MobileBottomNav } from "../MobileBottomNav";

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <PublicHeader />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <MobileBottomNav />
    </div>
  );
}
