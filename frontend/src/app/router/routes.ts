import { createElement } from "react";
import { type RouteObject } from "react-router-dom";

import { AppShell } from "@/components/layout/AppShell";
import { PlaceholderPage } from "@/components/shared/PlaceholderPage";
import { AssistantPage } from "@/features/assistant/pages/AssistantPage";
import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { PublicOnlyRoute } from "@/features/auth/components/PublicOnlyRoute";
import { AuthPage } from "@/features/auth/pages/AuthPage";
import { DashboardPage } from "@/features/dashboard/pages/DashboardPage";
import { DocumentsPage } from "@/features/documents/pages/DocumentsPage";

export const routes = [
  {
    path: "/",
    element: createElement(PublicOnlyRoute),
    children: [
      {
        index: true,
        element: createElement(AuthPage, { mode: "login" }),
      },
      {
        path: "login",
        element: createElement(AuthPage, { mode: "login" }),
      },
      {
        path: "register",
        element: createElement(AuthPage, { mode: "register" }),
      },
    ],
  },
  {
    element: createElement(ProtectedRoute),
    children: [
      {
        element: createElement(AppShell),
        children: [
          {
            path: "/dashboard",
            element: createElement(DashboardPage),
          },
          {
            path: "/documents",
            element: createElement(DocumentsPage),
          },
          {
            path: "/assistant",
            element: createElement(AssistantPage),
          },
          {
            path: "/assessments",
            element: createElement(PlaceholderPage, {
              title: "Evaluations",
              description:
                "Les evaluations et quiz personnalises ne sont pas encore implementes.",
            }),
          },
          {
            path: "/learning-plan",
            element: createElement(PlaceholderPage, {
              title: "Plan d'apprentissage",
              description:
                "Les parcours personnalises seront construits dans une fonctionnalite dediee.",
            }),
          },
          {
            path: "/soutenance",
            element: createElement(PlaceholderPage, {
              title: "Simulation de soutenance",
              description:
                "La simulation orale sera ajoutee sans execution d'agent dans cette etape.",
            }),
          },
          {
            path: "/reports",
            element: createElement(PlaceholderPage, {
              title: "Rapports",
              description:
                "Les rapports detailles seront branches quand les donnees reelles existeront.",
            }),
          },
          {
            path: "/settings",
            element: createElement(PlaceholderPage, {
              title: "Parametres",
              description:
                "Les preferences du compte seront traitees dans une etape ulterieure.",
            }),
          },
        ],
      },
    ],
  },
] satisfies RouteObject[];
