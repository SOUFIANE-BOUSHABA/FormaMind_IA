import { type RouteObject } from "react-router-dom";
import { createElement } from "react";

import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { PublicOnlyRoute } from "@/features/auth/components/PublicOnlyRoute";
import { AuthPage } from "@/features/auth/pages/AuthPage";
import { DashboardPlaceholderPage } from "@/features/dashboard/pages/DashboardPlaceholderPage";

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
        path: "/dashboard",
        element: createElement(DashboardPlaceholderPage),
      },
    ],
  },
] satisfies RouteObject[];
