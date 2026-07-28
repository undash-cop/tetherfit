import { BrowserRouter, Navigate, Route, Routes } from "react-router";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AdminShell } from "@/components/layout/AdminShell";
import { AppShell } from "@/components/layout/AppShell";
import { ClientShell } from "@/components/layout/ClientShell";
import { MarketingLayout } from "@/components/layout/MarketingLayout";
import { AuthCallbackPage } from "@/pages/auth/AuthCallbackPage";
import { LoginPage } from "@/pages/auth/LoginPage";
import { AdminFlagsPage } from "@/pages/admin/AdminFlagsPage";
import { AdminOrgsPage } from "@/pages/admin/AdminOrgsPage";
import { AdminSupportPage } from "@/pages/admin/AdminSupportPage";
import { AdminUsagePage } from "@/pages/admin/AdminUsagePage";
import { AiCopilotPage } from "@/pages/app/AiCopilotPage";
import { AnalyticsPage } from "@/pages/app/AnalyticsPage";
import { CalendarPage } from "@/pages/app/CalendarPage";
import { ClientCreatePage } from "@/pages/app/ClientCreatePage";
import { ClientDetailPage } from "@/pages/app/ClientDetailPage";
import { ClientsPage } from "@/pages/app/ClientsPage";
import { DashboardPage } from "@/pages/app/DashboardPage";
import { EnterprisePage } from "@/pages/app/EnterprisePage";
import { IntegrationsPage } from "@/pages/app/IntegrationsPage";
import { MarketplacePage } from "@/pages/app/MarketplacePage";
import { NutritionPage } from "@/pages/app/NutritionPage";
import { OnboardingPage } from "@/pages/app/OnboardingPage";
import { PaymentsPage } from "@/pages/app/PaymentsPage";
import { ReportsPage } from "@/pages/app/ReportsPage";
import { SessionDetailPage } from "@/pages/app/SessionDetailPage";
import { SchedulingPage } from "@/pages/app/SchedulingPage";
import { AutomationsPage } from "@/pages/app/AutomationsPage";
import { SettingsPage } from "@/pages/app/SettingsPage";
import { WorkoutsPage } from "@/pages/app/WorkoutsPage";
import { ClientBookPage } from "@/pages/client/ClientBookPage";
import { ClientHomePage } from "@/pages/client/ClientHomePage";
import { ClientNutritionPage } from "@/pages/client/ClientNutritionPage";
import { ClientPaymentsPage } from "@/pages/client/ClientPaymentsPage";
import { ClientProfilePage } from "@/pages/client/ClientProfilePage";
import { ClientProgressPage } from "@/pages/client/ClientProgressPage";
import { ClientWorkoutsPage } from "@/pages/client/ClientWorkoutsPage";
import { ContactPage } from "@/pages/public/ContactPage";
import { FeaturesPage } from "@/pages/public/FeaturesPage";
import { HomePage } from "@/pages/public/HomePage";
import { PricingPage } from "@/pages/public/PricingPage";
import { PublicMarketplaceDetailPage } from "@/pages/public/PublicMarketplaceDetailPage";
import { PublicMarketplacePage } from "@/pages/public/PublicMarketplacePage";
import { ChatPage } from "@/pages/shared/ChatPage";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MarketingLayout />}>
          <Route index element={<HomePage />} />
          <Route path="features" element={<FeaturesPage />} />
          <Route path="pricing" element={<PricingPage />} />
          <Route path="contact" element={<ContactPage />} />
          <Route path="marketplace" element={<PublicMarketplacePage />} />
          <Route path="marketplace/:slug" element={<PublicMarketplaceDetailPage />} />
        </Route>

        <Route path="login" element={<LoginPage />} />
        <Route path="auth/callback" element={<AuthCallbackPage />} />

        <Route element={<RequireAuth />}>
          <Route path="app/onboarding" element={<OnboardingPage />} />
          <Route path="app" element={<AppShell />}>
            <Route index element={<DashboardPage />} />
            <Route path="calendar" element={<CalendarPage />} />
            <Route path="clients" element={<ClientsPage />} />
            <Route path="clients/new" element={<ClientCreatePage />} />
            <Route path="clients/:id" element={<ClientDetailPage />} />
            <Route path="sessions/:id" element={<SessionDetailPage />} />
            <Route path="workouts" element={<WorkoutsPage />} />
            <Route path="nutrition" element={<NutritionPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="ai" element={<AiCopilotPage />} />
            <Route path="integrations" element={<IntegrationsPage />} />
            <Route path="marketplace" element={<MarketplacePage />} />
            <Route path="enterprise" element={<EnterprisePage />} />
            <Route path="chat" element={<ChatPage mode="trainer" />} />
            <Route path="scheduling" element={<SchedulingPage />} />
            <Route path="automations" element={<AutomationsPage />} />
            <Route path="payments" element={<PaymentsPage />} />
            <Route path="profile" element={<Navigate to="/app/settings" replace />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>

          <Route path="client" element={<ClientShell />}>
            <Route index element={<ClientHomePage />} />
            <Route path="workouts" element={<ClientWorkoutsPage />} />
            <Route path="nutrition" element={<ClientNutritionPage />} />
            <Route path="book" element={<ClientBookPage />} />
            <Route path="progress" element={<ClientProgressPage />} />
            <Route path="payments" element={<ClientPaymentsPage />} />
            <Route path="chat" element={<ChatPage mode="client" />} />
            <Route path="profile" element={<ClientProfilePage />} />
          </Route>

          <Route path="admin" element={<AdminShell />}>
            <Route index element={<AdminUsagePage />} />
            <Route path="organizations" element={<AdminOrgsPage />} />
            <Route path="flags" element={<AdminFlagsPage />} />
            <Route path="tickets" element={<AdminSupportPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
