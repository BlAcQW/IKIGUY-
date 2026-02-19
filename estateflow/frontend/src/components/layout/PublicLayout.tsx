import { Outlet } from "react-router-dom";
import { PublicHeader } from "./PublicHeader";
import { MobileBottomNav } from "../MobileBottomNav";

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-background">
      <PublicHeader />
      <main>
        <Outlet />
      </main>
      <MobileBottomNav />
    </div>
  );
}
