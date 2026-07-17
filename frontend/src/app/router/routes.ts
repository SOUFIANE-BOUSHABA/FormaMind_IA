import { type RouteObject } from "react-router-dom";
import { createElement } from "react";

import { FoundationPage } from "@/components/shared/FoundationPage";

export const routes = [
  {
    path: "/",
    element: createElement(FoundationPage),
  },
] satisfies RouteObject[];
