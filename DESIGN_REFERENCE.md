# FormaMind AI Design Reference

This file summarizes the Stitch export used as a visual reference. The generated HTML screens were inspected but not copied into the React application.

## Visual Identity

FormaMind AI should feel premium, calm, and educational: a modern SaaS interface with a disciplined layout, soft surfaces, and restrained AI accents. The Stitch design names this direction "L'Intelligence Sereine".

## Main Color Palette

- Primary indigo: `#3525CD`, with action surfaces around `#4F46E5`.
- AI violet accent: `#712AE2` and `#8A4CFC`.
- Knowledge/cyan accent: `#006A7C`, `#4CD7F6`, `#93E8FF`.
- Main background: `#F8FAFC` or the softer Stitch surface `#FAF8FF`.
- Secondary/sidebar background: `#F1F5F9`.
- Card surface: `#FFFFFF`.
- Text navy: `#131B2E`.
- Muted text: `#464555`.
- Border: `#E2E8F0`, `#CBD5E1`, and Stitch outline variants around `#C7C4D8`.
- Success: emerald/green.
- Warning: amber.
- Error: `#BA1A1A`.

## Typography

- Primary family: Manrope for page titles and body content.
- Secondary UI family: Inter for compact labels, badges, and code-like metadata.
- H1 direction: large, confident, heavy weight.
- Body copy: generous line height for learning content.
- Labels: uppercase or small semibold text with increased spacing only where it improves scanning.

## Spacing Principles

- Use a 4px base rhythm.
- Desktop content padding should generally start at 32px.
- Default gutters are 24px.
- Mobile content should reduce to 16px side padding.
- Dense learning tools can use tighter internal rhythm, but page composition should remain calm.

## Card Style

- White or subtly tinted surfaces.
- 1px borders.
- Dashboard cards generally use 16px radius.
- Inputs and precise controls use 8px radius.
- Badges use pill radii.
- AI-specific panels may use subtle glass effects and violet/cyan accent borders.

## Border Radii

- Small: 4px.
- Interactive controls: 8px.
- Medium surfaces: 12px.
- Dashboard cards: 16px.
- Hero/agent panels in Stitch sometimes use 24px to 40px; future implementation should use these only for immersive AI states.

## Shadows

- Base cards: `0 4px 20px rgba(15, 23, 42, 0.05)`.
- Elevated surfaces: `0 10px 40px rgba(15, 23, 42, 0.10)`.
- Primary actions may use a restrained indigo shadow on hover.

## Sidebar Pattern

- Fixed desktop sidebar around 280px wide.
- Background is a pale blue-gray or lavender-tinted surface.
- Active item uses a left indigo indicator and stronger navy/indigo text.
- Icons are 20px, preferably from Lucide.
- Bottom area contains help and sign-out actions.

## Top Navigation Pattern

- Sticky or fixed top bar.
- Search is central and rounded.
- Right side contains notifications/settings/profile.
- The bar can use translucent blur, but should remain subtle.

## Responsive Behavior

- Desktop: fixed sidebar and roomy content grid.
- Tablet: sidebar can collapse.
- Mobile: use a compact menu or bottom navigation in future feature work.
- Cards should reflow into fewer columns without losing readable spacing.

## Canonical Navigation Labels

Use these French labels consistently:

- Tableau de bord
- Documents
- Assistant pédagogique
- Évaluations
- Plan d'apprentissage
- Simulation de soutenance
- Rapports
- Paramètres

Use one consistent future demo identity:

- Rabie
- Apprenant en Intelligence Artificielle

This identity is documented only and is not implemented in the current frontend.

## Preferred Screen Variants

- Dashboard: prefer `tableau_de_bord_premium_formamind_ai` for its stronger KPI and agent activity treatment.
- Assistant: prefer `assistant_p_dagogique_pro_formamind_ai` for its three-column learning assistant structure.
- Learning plan: prefer `plan_d_apprentissage_expert_formamind_ai` for its clearer roadmap hierarchy.
- Soutenance: prefer `simulation_de_soutenance_elite_formamind_ai` for its focused oral simulation state.
- Documents: the base `mes_documents_formamind_ai` screen is the clearest document-management reference.
- Login and logo exports are useful for brand tone only; authentication is out of scope.

## Known Visual Inconsistencies

- The export alternates between "Assistant", "Assistant IA", and the requested canonical "Assistant pédagogique".
- The export alternates between "Planification" and "Plan d'apprentissage".
- Demo identities vary across screens.
- Some screens use larger radii than the design notes recommend for ordinary cards.
- Some HTML uses decorative glows and blurred shapes; these should be reserved for AI states, not base layout.
- Several generated screens include product features that are explicitly out of scope for the current foundation.

## Rules For Future Features

- Treat Stitch as visual source of truth, not as source code.
- Do not paste generated static HTML into React.
- Keep visible text in French.
- Keep AI accents meaningful and restrained.
- Prefer Lucide icons.
- Keep route components thin and feature logic isolated.
- Use typed services and TanStack Query for frontend data access.
- Preserve the distinction between static educational content and active AI assistance.
