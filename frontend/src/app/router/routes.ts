import { createElement } from "react";
import { type RouteObject } from "react-router-dom";

import { AppShell } from "@/components/layout/AppShell";
import { PlaceholderPage } from "@/components/shared/PlaceholderPage";
import { AssessmentsPage } from "@/features/assessments/pages/AssessmentsPage";
import { QuizPage } from "@/features/assessments/pages/QuizPage";
import { ResultsPage } from "@/features/assessments/pages/ResultsPage";
import { AssistantPage } from "@/features/assistant/pages/AssistantPage";
import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { PublicOnlyRoute } from "@/features/auth/components/PublicOnlyRoute";
import { AuthPage } from "@/features/auth/pages/AuthPage";
import { DashboardPage } from "@/features/dashboard/pages/DashboardPage";
import { DocumentsPage } from "@/features/documents/pages/DocumentsPage";
import { GenerateLearningPlanPage } from "@/features/learning-plan/pages/GenerateLearningPlanPage";
import { LearningPlanDetailPage } from "@/features/learning-plan/pages/LearningPlanDetailPage";
import { LearningPlansPage } from "@/features/learning-plan/pages/LearningPlansPage";
import { SoutenanceResultsPage } from "@/features/soutenance/pages/SoutenanceResultsPage";
import { SoutenanceSessionPage } from "@/features/soutenance/pages/SoutenanceSessionPage";
import { SoutenanceSessionsPage } from "@/features/soutenance/pages/SoutenanceSessionsPage";

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
            element: createElement(AssessmentsPage),
          },
          {
            path: "/attempts/:attemptId",
            element: createElement(QuizPage),
          },
          {
            path: "/attempts/:attemptId/results",
            element: createElement(ResultsPage),
          },
          {
            path: "/learning-plan",
            element: createElement(LearningPlansPage),
          },
          {
            path: "/learning-plans/new/:attemptId",
            element: createElement(GenerateLearningPlanPage),
          },
          {
            path: "/learning-plans/:planId",
            element: createElement(LearningPlanDetailPage),
          },
          {
            path: "/soutenance",
            element: createElement(SoutenanceSessionsPage),
          },
          {
            path: "/soutenance/:sessionId",
            element: createElement(SoutenanceSessionPage),
          },
          {
            path: "/soutenance/:sessionId/results",
            element: createElement(SoutenanceResultsPage),
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
