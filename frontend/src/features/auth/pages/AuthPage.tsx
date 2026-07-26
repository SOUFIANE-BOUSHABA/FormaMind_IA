import { zodResolver } from "@hookform/resolvers/zod";
import { BookOpen, Bot, Eye, EyeOff, LogIn, Mail, UserPlus } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";

import { ApiError, ApiNetworkError } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { useAuth } from "@/features/auth/hooks/useAuth";
import {
  loginSchema,
  registerSchema,
  type LoginFormValues,
  type RegisterFormValues,
} from "@/features/auth/schemas/auth-schemas";

type AuthMode = "login" | "register";

type AuthPageProps = {
  mode: AuthMode;
};

type AuthFormValues = LoginFormValues | RegisterFormValues;

function isRegisterMode(mode: AuthMode): mode is "register" {
  return mode === "register";
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiNetworkError) {
    return "Le backend ne repond pas. Verifiez qu'il est lance puis reessayez.";
  }

  if (error instanceof ApiError) {
    if (error.status === 401) {
      return "Identifiants incorrects.";
    }

    if (error.status === 409) {
      return "Cette adresse e-mail est déjà utilisée.";
    }

    return "Connexion au serveur impossible.";
  }

  return "Connexion au serveur impossible.";
}

export function AuthPage({ mode }: AuthPageProps) {
  const auth = useAuth();
  const navigate = useNavigate();
  const [formError, setFormError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const isRegister = isRegisterMode(mode);

  const form = useForm<AuthFormValues>({
    defaultValues: isRegister
      ? { email: "", fullName: "", password: "" }
      : { email: "", password: "" },
    resolver: zodResolver(isRegister ? registerSchema : loginSchema),
  });

  async function onSubmit(values: AuthFormValues) {
    setFormError(null);

    try {
      if (isRegister) {
        const registerValues = values as RegisterFormValues;
        await auth.register({
          email: registerValues.email,
          fullName: registerValues.fullName,
          password: registerValues.password,
        });
      } else {
        await auth.login(values);
      }

      navigate("/dashboard", { replace: true });
    } catch (error) {
      setFormError(getErrorMessage(error));
    }
  }

  const isSubmitting = form.formState.isSubmitting;

  return (
    <main className="min-h-screen overflow-hidden bg-[rgb(var(--color-surface-ai))] text-foreground">
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-24 -top-24 h-80 w-80 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute -bottom-24 -right-24 h-96 w-96 rounded-full bg-secondary/10 blur-3xl" />
      </div>

      <section className="mx-auto grid min-h-screen w-full max-w-6xl grid-cols-1 items-center gap-12 px-6 py-10 lg:grid-cols-12 lg:px-8">
        <div className="order-2 flex flex-col gap-10 lg:order-1 lg:col-span-7">
          <div className="max-w-xl space-y-5">
            <h1 className="font-heading text-4xl font-extrabold leading-tight text-foreground md:text-5xl">
              Transformez vos supports de formation en parcours
              d’apprentissage personnalisé.
            </h1>
            <p className="max-w-md text-lg leading-8 text-foreground/65">
              L’intelligence artificielle au service de l’excellence
              pédagogique.
            </p>
          </div>

          <div className="relative min-h-[360px] max-w-2xl">
            <div className="absolute left-[34%] top-8 z-10 flex h-56 w-40 -rotate-2 flex-col rounded-xl border border-border bg-white p-5 shadow-elevated transition-transform hover:rotate-0">
              <div className="mb-3 h-2 w-16 rounded-full bg-primary/20" />
              <div className="mb-2 h-1.5 w-full rounded-full bg-primary/10" />
              <div className="mb-2 h-1.5 w-full rounded-full bg-primary/10" />
              <div className="mb-5 h-1.5 w-3/4 rounded-full bg-primary/10" />
              <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed border-border bg-surface-muted">
                <BookOpen className="h-9 w-9 text-primary/40" />
              </div>
              <div className="mt-4 flex items-center gap-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <Bot className="h-3.5 w-3.5" />
                </span>
                <span className="font-ui text-[10px] font-bold uppercase tracking-widest text-primary">
                  Analyse active
                </span>
              </div>
            </div>

            <div className="absolute left-4 top-10 flex flex-col items-center gap-2">
              <div className="flex h-20 w-20 items-center justify-center rounded-2xl border border-white/70 border-l-4 border-l-accent bg-white/75 shadow-card backdrop-blur">
                <BookOpen className="h-9 w-9 text-accent" />
              </div>
              <span className="rounded-full bg-[rgb(var(--color-accent-soft))] px-3 py-1 font-ui text-sm font-semibold text-accent">
                Connaissance
              </span>
            </div>

            <div className="absolute bottom-10 left-0 flex flex-col items-center gap-2">
              <div className="flex h-20 w-20 items-center justify-center rounded-2xl border border-white/70 border-l-4 border-l-primary bg-white/75 shadow-card backdrop-blur">
                <UserPlus className="h-9 w-9 text-primary" />
              </div>
              <span className="rounded-full bg-primary/10 px-3 py-1 font-ui text-sm font-semibold text-primary">
                Évaluation
              </span>
            </div>

            <div className="absolute right-10 top-20 flex flex-col items-center gap-2">
              <div className="flex h-24 w-24 items-center justify-center rounded-2xl border border-white/70 border-l-4 border-l-secondary bg-white/75 shadow-card backdrop-blur">
                <Bot className="h-11 w-11 text-secondary" />
              </div>
              <span className="rounded-full bg-secondary/10 px-3 py-1 font-ui text-sm font-semibold text-secondary">
                Coach d’apprentissage
              </span>
            </div>

           </div>
        </div>

        <div className="order-1 lg:order-2 lg:col-span-5">
          <div className="mx-auto w-full max-w-md border border-border bg-white p-8 shadow-card sm:p-10">
            <div className="mb-10 flex items-center justify-center gap-3 text-center">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-card">
                <Bot className="h-6 w-6" />
              </div>
              <div className="text-left">
                <p className="font-heading text-xl font-extrabold leading-none">
                  FormaMind AI
                </p>
                <p className="mt-1 font-ui text-xs font-semibold text-foreground/55">
                  Intelligence Éducative
                </p>
              </div>
            </div>

            <div className="mb-8 space-y-2 text-center">
              <h2 className="font-heading text-2xl font-bold">
                {isRegister ? "Créer votre compte" : "Bon retour parmi nous"}
              </h2>
              <p className="text-sm text-foreground/60">
                {isRegister
                  ? "Rejoignez votre espace FormaMind AI."
                  : "Connectez-vous à votre espace FormaMind AI."}
              </p>
            </div>

            <form className="space-y-5" onSubmit={form.handleSubmit(onSubmit)}>
              {isRegister ? (
                <label className="block space-y-2">
                  <span className="font-ui text-sm font-semibold">
                    Nom complet
                  </span>
                  <input
                    className="w-full rounded-lg border border-border bg-white px-4 py-3 outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/20"
                    placeholder="Rabie"
                    {...form.register("fullName")}
                  />
                  {"fullName" in form.formState.errors ? (
                    <span className="text-sm text-error">
                      {form.formState.errors.fullName?.message}
                    </span>
                  ) : null}
                </label>
              ) : null}

              <label className="block space-y-2">
                <span className="font-ui text-sm font-semibold">
                  Adresse e-mail
                </span>
                <div className="relative">
                  <input
                    className="w-full rounded-lg border border-border bg-white px-4 py-3 pr-11 outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/20"
                    placeholder="nom@entreprise.com"
                    type="email"
                    {...form.register("email")}
                  />
                  <Mail className="absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-foreground/45" />
                </div>
                {form.formState.errors.email?.message ? (
                  <span className="text-sm text-error">
                    {form.formState.errors.email.message}
                  </span>
                ) : null}
              </label>

              <label className="block space-y-2">
                <span className="font-ui text-sm font-semibold">
                  Mot de passe
                </span>
                <div className="relative">
                  <input
                    className="w-full rounded-lg border border-border bg-white px-4 py-3 pr-11 outline-none transition focus:border-primary focus:ring-4 focus:ring-primary/20"
                    placeholder="••••••••"
                    type={showPassword ? "text" : "password"}
                    {...form.register("password")}
                  />
                  <button
                    aria-label={
                      showPassword
                        ? "Masquer le mot de passe"
                        : "Afficher le mot de passe"
                    }
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-foreground/45 transition hover:text-primary"
                    onClick={() => {
                      setShowPassword((current) => !current);
                    }}
                    type="button"
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5" />
                    ) : (
                      <Eye className="h-5 w-5" />
                    )}
                  </button>
                </div>
                {form.formState.errors.password?.message ? (
                  <span className="text-sm text-error">
                    {form.formState.errors.password.message}
                  </span>
                ) : null}
              </label>

              {formError ? (
                <p className="rounded-lg border border-error/20 bg-error/5 px-4 py-3 text-sm font-medium text-error">
                  {formError}
                </p>
              ) : null}

              <button
                className={cn(
                  "flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-5 py-3.5 font-ui text-base font-bold text-primary-foreground shadow-elevated transition",
                  "hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-70",
                )}
                disabled={isSubmitting}
                type="submit"
              >
                {isSubmitting
                  ? "Connexion en cours..."
                  : isRegister
                    ? "Créer le compte"
                    : "Se connecter"}
                <LogIn className="h-5 w-5" />
              </button>
            </form>

            <p className="mt-8 text-center text-sm text-foreground/60">
              {isRegister ? "Vous avez déjà un compte ?" : "Pas encore de compte ?"}{" "}
              <Link
                className="font-bold text-primary transition hover:text-secondary"
                to={isRegister ? "/login" : "/register"}
              >
                {isRegister ? "Connectez-vous" : "Créer un compte"}
              </Link>
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
