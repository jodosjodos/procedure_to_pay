import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  FileText,
  CheckCircle,
  Users,
  TrendingUp,
  ArrowRight,
  ShieldCheck,
  Zap,
  Twitter,
  Github,
  Linkedin,
} from "lucide-react";

const Index = () => {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur-sm">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link
            to="/"
            className="flex items-center gap-2 text-lg font-semibold"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileText className="h-6 w-6" />
            </div>
            <span className="font-bold">ProcurePay</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
            <Link to="#features" className="text-muted-foreground transition-colors hover:text-foreground">Features</Link>
            <Link to="#pricing" className="text-muted-foreground transition-colors hover:text-foreground">Pricing</Link>
            <Link to="#contact" className="text-muted-foreground transition-colors hover:text-foreground">Contact</Link>
          </nav>
          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link to="/login">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <section className="container mx-auto px-4 py-16 sm:py-24 text-center">
          <Badge>Procure-to-Pay Platform</Badge>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold mt-6 tracking-tighter">
            Unified Procurement for Modern Teams
          </h1>
          <p className="max-w-3xl mx-auto mt-6 text-lg text-muted-foreground">
            ProcurePay streamlines approvals, purchase orders, and vendor
            management into one intuitive workspace, giving you control without
            slowing you down.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <Link to="/login">
              <Button size="lg">
                Get Started Free <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Button size="lg" variant="outline">
              Request a Demo
            </Button>
          </div>
          <div className="mt-12">
            <img
              src="/splash.jpg"
              alt="ProcurePay Dashboard"
              className="rounded-lg shadow-xl"
            />
          </div>
        </section>

        <section id="features" className="container mx-auto px-4 py-24 space-y-16">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold">Why ProcurePay?</h2>
            <p className="max-w-2xl mx-auto text-muted-foreground">
              Everything you need to manage company spending, from request to reconciliation.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard
              icon={Zap}
              title="Automated Workflows"
              description="Configure custom, multi-level approval chains that route requests to the right people, every time."
            />
            <FeatureCard
              icon={FileText}
              title="AI-Powered Document Processing"
              description="Instantly extract data from invoices and receipts, eliminating manual entry and reducing errors."
            />
            <FeatureCard
              icon={Users}
              title="Centralized Vendor Management"
              description="Onboard, manage, and communicate with all your vendors from a single, unified directory."
            />
            <FeatureCard
              icon={TrendingUp}
              title="Real-time Spend Visibility"
              description="Track budgets, monitor spending, and forecast expenses with powerful, easy-to-understand dashboards."
            />
            <FeatureCard
              icon={ShieldCheck}
              title="Audit-Ready Compliance"
              description="Maintain a complete, chronological record of every purchase for hassle-free audits."
            />
            <FeatureCard
              icon={CheckCircle}
              title="Seamless Integrations"
              description="Connect ProcurePay to your existing accounting software and ERP systems for a seamless data flow."
            />
          </div>
        </section>

        <section className="bg-secondary">
          <div className="container mx-auto px-4 py-24 text-center">
            <h2 className="text-3xl md:text-4xl font-bold">
              Ready to take control of your spending?
            </h2>
            <p className="max-w-2xl mx-auto mt-4 text-muted-foreground">
              Join hundreds of companies that trust ProcurePay to manage their
              procurement process from end to end.
            </p>
            <div className="mt-8">
              <Link to="/login">
                <Button size="lg">
                  Sign Up for Free <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t">
        <div className="container mx-auto px-4 py-8 md:py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="space-y-4">
              <Link
                to="/"
                className="flex items-center gap-2 text-lg font-semibold"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <FileText className="h-6 w-6" />
                </div>
                <span className="font-bold">ProcurePay</span>
              </Link>
              <p className="text-sm text-muted-foreground">
                The best way to manage your company's procurement.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2">
                <li><Link to="#features" className="text-sm text-muted-foreground hover:text-foreground">Features</Link></li>
                <li><Link to="#pricing" className="text-sm text-muted-foreground hover:text-foreground">Pricing</Link></li>
                <li><Link to="/dashboard" className="text-sm text-muted-foreground hover:text-foreground">Dashboard</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2">
                <li><Link to="#" className="text-sm text-muted-foreground hover:text-foreground">About Us</Link></li>
                <li><Link to="#" className="text-sm text-muted-foreground hover:text-foreground">Careers</Link></li>
                <li><Link to="#" className="text-sm text-muted-foreground hover:text-foreground">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2">
                <li><Link to="#" className="text-sm text-muted-foreground hover:text-foreground">Privacy Policy</Link></li>
                <li><Link to="#" className="text-sm text-muted-foreground hover:text-foreground">Terms of Service</Link></li>
              </ul>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-muted-foreground">&copy; 2024 ProcurePay. All rights reserved.</p>
            <div className="flex gap-4">
              <Link to="#" className="text-muted-foreground hover:text-foreground"><Twitter className="h-5 w-5" /></Link>
              <Link to="#" className="text-muted-foreground hover:text-foreground"><Github className="h-5 w-5" /></Link>
              <Link to="#" className="text-muted-foreground hover:text-foreground"><Linkedin className="h-5 w-5" /></Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

const Badge = ({ children }: { children: React.ReactNode }) => (
  <span className="inline-flex items-center rounded-full bg-primary/10 px-4 py-1 text-sm font-semibold text-primary">
    {children}
  </span>
);

const FeatureCard = ({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
}) => (
  <div className="p-6 rounded-lg border bg-card text-card-foreground text-center">
    <div className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 mb-4">
      <Icon className="h-6 w-6 text-primary" />
    </div>
    <h3 className="text-xl font-semibold">{title}</h3>
    <p className="mt-2 text-muted-foreground">{description}</p>
  </div>
);

export default Index;
