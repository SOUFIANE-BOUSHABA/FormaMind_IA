import { type RouteObject } from "react-router-dom";
import { createElement } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { PlaceholderPage } from "@/components/shared/PlaceholderPage";
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
            element: createElement(PlaceholderPage, {
              title: "Assistant pédagogique",
              description:
                "L'assistant IA restera séparé du tableau de bord et sera intégré plus tard.",
            }),
          },
          {
            path: "/assessments",
            element: createElement(PlaceholderPage, {
              title: "Évaluations",
              description:
                "Les évaluations et quiz personnalisés ne sont pas encore implémentés.",
            }),
          },
          {
            path: "/learning-plan",
            element: createElement(PlaceholderPage, {
              title: "Plan d'apprentissage",
              description:
                "Les parcours personnalisés seront construits dans une fonctionnalité dédiée.",
            }),
          },
          {
            path: "/soutenance",
            element: createElement(PlaceholderPage, {
              title: "Simulation de soutenance",
              description:
                "La simulation orale sera ajoutée sans exécution d'agent dans cette étape.",
            }),
          },
          {
            path: "/reports",
            element: createElement(PlaceholderPage, {
              title: "Rapports",
              description:
                "Les rapports détaillés seront branchés quand les données réelles existeront.",
            }),
          },
          {
            path: "/settings",
            element: createElement(PlaceholderPage, {
              title: "Paramètres",
              description:
                "Les préférences du compte seront traitées dans une étape ultérieure.",
            }),
          },
        ],
      },
    ],
  },
] satisfies RouteObject[];
