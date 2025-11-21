import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis, Cell } from "recharts";
import { Layout } from "@/components/Layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { requestsAPI } from "@/lib/api";
import { PurchaseRequest } from "@/types";
import {
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  Plus,
  Inbox,
  ArrowRight,
} from "lucide-react";
import { Link } from "react-router-dom";
import { StatusBadge } from "@/components/StatusBadge";
import { Skeleton } from "@/components/ui/skeleton";

const chartConfig = {
  requests: {
    label: "Requests",
  },
  pending: {
    label: "Pending",
    color: "hsl(var(--chart-1))",
  },
  approved: {
    label: "Approved",
    color: "hsl(var(--chart-2))",
  },
  rejected: {
    label: "Rejected",
    color: "hsl(var(--chart-3))",
  },
};

const Dashboard = () => {
  const { user } = useAuth();
  const [requests, setRequests] = useState<PurchaseRequest[]>([]);
  const [loading, setLoading] = useState(true);

  const stats = useMemo(() => {
    return {
      total: requests.length,
      pending: requests.filter((r) => r.status === "pending").length,
      approved: requests.filter((r) => r.status === "approved").length,
      rejected: requests.filter((r) => r.status === "rejected").length,
    };
  }, [requests]);
  
  const chartData = useMemo(() => ([
    { status: "pending", value: stats.pending, fill: "hsl(var(--pending))" },
    { status: "approved", value: stats.approved, fill: "hsl(var(--approved))" },
    { status: "rejected", value: stats.rejected, fill: "hsl(var(--rejected))" },
  ]), [stats]);

  useEffect(() => {
    const fetchRequests = async () => {
      setLoading(true);
      try {
        const data = await requestsAPI.list();
        setRequests(data);
      } catch (error) {
        console.error("Failed to fetch requests:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchRequests();
  }, []);

  const recentRequests = useMemo(() => requests.slice(0, 5), [requests]);
  const approvalRate = stats.total
    ? Math.round((stats.approved / stats.total) * 100)
    : 0;

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  return (
    <Layout>
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">
              {getGreeting()}, {user?.name || "there"}!
            </h1>
            <p className="text-muted-foreground">
              Here's what's happening with your procurement today.
            </p>
          </div>
          {user?.role === "staff" && (
            <Link to="/requests/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Request
              </Button>
            </Link>
          )}
        </div>

        <section className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4">
          {[
            {
              label: "Total Requests",
              value: stats.total,
              icon: <FileText className="h-6 w-6 text-muted-foreground" />,
              trend: `${
                stats.total ? `${approvalRate}% approval rate` : "No data yet"
              }`,
            },
            {
              label: "Pending",
              value: stats.pending,
              icon: <Clock className="h-6 w-6 text-yellow-500" />,
              trend: stats.pending ? "Awaiting action" : "All caught up",
            },
            {
              label: "Approved",
              value: stats.approved,
              icon: <CheckCircle className="h-6 w-6 text-green-500" />,
              trend: stats.approved ? "Ready for finance" : "No approvals yet",
            },
            {
              label: "Rejected",
              value: stats.rejected,
              icon: <XCircle className="h-6 w-6 text-red-500" />,
              trend: stats.rejected ? "Needs attention" : "Zero escalations",
            },
          ].map((card) => (
            <Card key={card.label}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {card.label}
                </CardTitle>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  {card.icon}
                </div>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-8 w-1/2" />
                ) : (
                  <div className="text-2xl font-bold">{card.value}</div>
                )}
                <p className="text-xs text-muted-foreground">{card.trend}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Recent Requests</CardTitle>
              <CardDescription>
                {loading
                  ? "Fetching your latest activity…"
                  : `${
                      recentRequests.length || "No"
                    } new requests in this cycle.`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : recentRequests.length === 0 ? (
                <div className="flex h-40 flex-col items-center justify-center rounded-lg border-2 border-dashed text-center">
                  <Inbox className="h-10 w-10 text-muted-foreground" />
                  <p className="mt-2 text-muted-foreground">
                    No requests yet. Create one to get started!
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {recentRequests.map((request) => (
                    <Link
                      key={request.id}
                      to={`/requests/${request.id}`}
                      className="group"
                    >
                      <div className="flex items-center justify-between rounded-lg border p-4 transition-all hover:bg-accent hover:shadow-md">
                        <div className="flex items-center gap-4">
                          <div
                            className={`h-10 w-10 flex items-center justify-center rounded-lg bg-opacity-20 bg-${
                              request.status === "approved"
                                ? "green"
                                : request.status === "rejected"
                                ? "red"
                                : "yellow"
                            }-100`}
                          >
                            <FileText
                              className={`h-5 w-5 text-${
                                request.status === "approved"
                                  ? "green"
                                  : request.status === "rejected"
                                  ? "red"
                                  : "yellow"
                              }-600`}
                            />
                          </div>
                          <div>
                            <p className="font-semibold">{request.title}</p>
                            <p className="text-sm text-muted-foreground">
                              ${request.amount.toLocaleString()} •{" "}
                              {new Date(
                                request.created_at
                              ).toLocaleDateString()} by {request.created_by_name}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <StatusBadge status={request.status} />
                          <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-1" />
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Request Overview</CardTitle>
              <CardDescription>
                A summary of your request statuses.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  <Skeleton className="h-48 w-full" />
                </div>
              ) : (
                <ChartContainer config={chartConfig} className="h-48 w-full">
                  <BarChart data={chartData} margin={{ top: 20, right: 20, bottom: 0, left: 0 }} accessibilityLayer>
                    <CartesianGrid vertical={false} />
                    <XAxis
                      dataKey="status"
                      tickLine={false}
                      tickMargin={10}
                      axisLine={false}
                      tickFormatter={(value) =>
                        value.slice(0, 3).toUpperCase()
                      }
                    />
                    <YAxis />
                    <ChartTooltip
                      cursor={false}
                      content={<ChartTooltipContent indicator="dot" />}
                    />
                    <Bar
                      dataKey="value"
                      radius={4}
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ChartContainer>
              )}
            </CardContent>
          </Card>
        </section>
      </div>
    </Layout>
  );
};

export default Dashboard;
