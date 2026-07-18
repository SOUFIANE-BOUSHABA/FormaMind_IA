import { Sparkles } from "lucide-react";

type PlaceholderPageProps = {
  title: string;
  description: string;
};

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <div className="px-4 py-8 pb-28 lg:px-10 lg:py-10">
      <section className="rounded-[28px] border border-border bg-white p-8 shadow-card">
        <div className="flex max-w-2xl flex-col gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <p className="font-ui text-xs font-bold uppercase tracking-[0.22em] text-primary">
              FormaMind AI
            </p>
            <h1 className="mt-2 font-heading text-3xl font-extrabold">
              {title}
            </h1>
          </div>
          <p className="text-foreground/65">{description}</p>
        </div>
      </section>
    </div>
  );
}
