import { useEffect, useRef } from "react";
import { ClerkProvider, SignIn, SignUp, Show, useClerk, useUser } from "@clerk/react";
import { publishableKeyFromHost } from "@clerk/react/internal";
import { shadcn } from "@clerk/themes";
import { QueryClient, QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import { Switch, Route, Redirect, Link, useLocation, Router as WouterRouter } from "wouter";
import type { ReactNode } from "react";
import LandingPage from "@/pages/LandingPage";

const clerkPubKey = publishableKeyFromHost(
  window.location.hostname,
  import.meta.env.VITE_CLERK_PUBLISHABLE_KEY,
);
const clerkProxyUrl = import.meta.env.VITE_CLERK_PROXY_URL;
const basePath = import.meta.env.BASE_URL.replace(/\/$/, "");
const queryClient = new QueryClient();

function stripBase(path: string): string {
  return basePath && path.startsWith(basePath)
    ? path.slice(basePath.length) || "/"
    : path;
}

if (!clerkPubKey) {
  throw new Error("Missing VITE_CLERK_PUBLISHABLE_KEY");
}

const clerkAppearance = {
  theme: shadcn,
  cssLayerName: "clerk",
  options: {
    logoPlacement: "inside" as const,
    logoLinkUrl: basePath || "/",
    logoImageUrl: `${window.location.origin}${basePath}/logo.svg`,
  },
  variables: {
    colorPrimary: "#c2410c",
    colorForeground: "#2e201a",
    colorMutedForeground: "#78675c",
    colorDanger: "#b91c1c",
    colorBackground: "#fffaf2",
    colorInput: "#ffffff",
    colorInputForeground: "#2e201a",
    colorNeutral: "#5b4639",
    fontFamily: "Poppins, sans-serif",
    borderRadius: "0.75rem",
  },
  elements: {
    rootBox: "w-full flex justify-center",
    cardBox: "bg-[#fffaf2] rounded-2xl w-[440px] max-w-full overflow-hidden shadow-xl border border-orange-100",
    card: "!shadow-none !border-0 !bg-transparent !rounded-none",
    footer: "!shadow-none !border-0 !bg-transparent !rounded-none",
    headerTitle: "text-[#2e201a] font-bold",
    headerSubtitle: "text-[#78675c]",
    socialButtonsBlockButtonText: "text-[#2e201a]",
    formFieldLabel: "text-[#2e201a]",
    footerActionLink: "text-orange-800 font-semibold",
    footerActionText: "text-[#78675c]",
    dividerText: "text-[#78675c]",
    identityPreviewEditButton: "text-orange-800",
    formFieldSuccessText: "text-green-800",
    alertText: "text-red-800",
    logoBox: "mb-6",
    logoImage: "h-14 w-auto",
    socialButtonsBlockButton: "bg-white border-orange-200",
    formButtonPrimary: "bg-orange-700 text-white font-semibold",
    formFieldInput: "bg-white text-[#2e201a] border-orange-200",
    footerAction: "bg-orange-50",
    dividerLine: "bg-orange-200",
    alert: "bg-red-50 border-red-200",
    otpCodeFieldInput: "bg-white text-[#2e201a] border-orange-200",
    formFieldRow: "mb-4",
    main: "gap-5",
  },
};

function AuthPage({ mode }: { mode: "sign-in" | "sign-up" }) {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-orange-50 via-amber-50 to-red-50 px-4 py-12">
      <Link href="/" className="mb-6 text-sm font-medium text-orange-800 hover:underline">Back to the game</Link>
      {mode === "sign-in" ? (
        <SignIn routing="path" path={`${basePath}/sign-in`} signUpUrl={`${basePath}/sign-up`} />
      ) : (
        <SignUp routing="path" path={`${basePath}/sign-up`} signInUrl={`${basePath}/sign-in`} />
      )}
    </main>
  );
}

function AccountBar() {
  const { user } = useUser();
  const { signOut } = useClerk();
  const name = user?.firstName || user?.primaryEmailAddress?.emailAddress || "Player";

  return (
    <header className="relative z-40 flex items-center justify-end gap-3 border-b border-orange-100 bg-[#fffaf2] px-4 py-3 text-sm">
      <span className="truncate max-w-56 text-muted-foreground" data-testid="account-name">{name}</span>
      <button type="button" data-testid="button-sign-out" onClick={() => void signOut({ redirectUrl: basePath || "/" })} className="shrink-0 rounded-lg border border-orange-200 px-3 py-1.5 font-semibold text-orange-800 hover:bg-orange-50">
        Sign out
      </button>
    </header>
  );
}

function ClerkQueryClientCacheInvalidator() {
  const { addListener } = useClerk();
  const queryClient = useQueryClient();
  const prevUserIdRef = useRef<string | null | undefined>(undefined);

  useEffect(() => {
    const unsubscribe = addListener(({ user }) => {
      const userId = user?.id ?? null;
      if (prevUserIdRef.current !== undefined && prevUserIdRef.current !== userId) {
        queryClient.clear();
      }
      prevUserIdRef.current = userId;
    });
    return unsubscribe;
  }, [addListener, queryClient]);

  return null;
}

function ClerkProviderWithRoutes({ game, toaster }: { game: ReactNode; toaster: ReactNode }) {
  const [, setLocation] = useLocation();
  return (
    <ClerkProvider
      publishableKey={clerkPubKey}
      proxyUrl={clerkProxyUrl}
      appearance={clerkAppearance}
      signInUrl={`${basePath}/sign-in`}
      signUpUrl={`${basePath}/sign-up`}
      signInFallbackRedirectUrl={`${basePath}/play`}
      signUpFallbackRedirectUrl={`${basePath}/play`}
      localization={{
        signIn: { start: { title: "Welcome back", subtitle: "Sign in to start your next game" } },
        signUp: { start: { title: "Join the game", subtitle: "Create your account to play Indian Dumb Charades" } },
      }}
      routerPush={(to) => setLocation(stripBase(to))}
      routerReplace={(to) => setLocation(stripBase(to), { replace: true })}
    >
      <QueryClientProvider client={queryClient}>
        <ClerkQueryClientCacheInvalidator />
        <Switch>
          <Route path="/">
            <Show when="signed-in"><Redirect to="/play" /></Show>
            <Show when="signed-out"><LandingPage /></Show>
          </Route>
          <Route path="/sign-in/*?"><AuthPage mode="sign-in" /></Route>
          <Route path="/sign-up/*?"><AuthPage mode="sign-up" /></Route>
          <Route path="/play">
            <Show when="signed-in"><AccountBar />{game}</Show>
            <Show when="signed-out"><Redirect to="/" /></Show>
          </Route>
          <Route><Redirect to="/" /></Route>
        </Switch>
        {toaster}
      </QueryClientProvider>
    </ClerkProvider>
  );
}

export default function AuthRoutes(props: { game: ReactNode; toaster: ReactNode }) {
  return (
    <WouterRouter base={basePath}>
      <ClerkProviderWithRoutes {...props} />
    </WouterRouter>
  );
}
