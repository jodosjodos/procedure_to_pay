import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Layout } from "@/components/Layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/StatusBadge";
import { requestsAPI } from "@/lib/api";
import { PurchaseRequest } from "@/types";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import {
  FileText,
  DollarSign,
  Calendar,
  User,
  CheckCircle,
  XCircle,
  Upload,
  Download,
  ArrowLeft,
  MessageSquare,
} from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

const RequestDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [request, setRequest] = useState<PurchaseRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [comment, setComment] = useState("");
  const [receipt, setReceipt] = useState<File | null>(null);

  useEffect(() => {
    const fetchRequest = async () => {
      if (!id) return;
      setLoading(true);
      try {
        const data = await requestsAPI.get(id);
        setRequest(data);
      } catch (error) {
        console.error("Failed to fetch request:", error);
        toast({
          title: "Error",
          description: "Failed to load request details.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchRequest();
  }, [id, toast]);

  const handleAction = async (action: "approve" | "reject") => {
    if (!id) return;
    setActionLoading(true);

    try {
      const apiCall =
        action === "approve"
          ? requestsAPI.approve(id, comment || undefined)
          : requestsAPI.reject(id, comment || undefined);
      await apiCall;
      toast({
        title: `Request ${action}d`,
        description: `The purchase request has been ${action}d.`,
      });
      const data = await requestsAPI.get(id);
      setRequest(data);
      setComment("");
    } catch (error) {
      toast({
        title: `Failed to ${action} request`,
        description:
          error instanceof Error ? error.message : "An error occurred.",
        variant: "destructive",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmitReceipt = async () => {
    if (!id || !receipt) return;
    setActionLoading(true);

    try {
      await requestsAPI.submitReceipt(id, receipt);
      toast({
        title: "Receipt submitted",
        description: "Your receipt has been uploaded successfully.",
      });
      const data = await requestsAPI.get(id);
      setRequest(data);
      setReceipt(null);
    } catch (error) {
      toast({
        title: "Failed to submit receipt",
        description:
          error instanceof Error ? error.message : "An error occurred.",
        variant: "destructive",
      });
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6">
          <Skeleton className="h-8 w-1/4" />
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-6">
              <Skeleton className="h-64 w-full" />
              <Skeleton className="h-48 w-full" />
            </div>
            <div className="space-y-6">
              <Skeleton className="h-96 w-full" />
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (!request) {
    return (
      <Layout>
        <div className="py-20 text-center">
          <h2 className="text-2xl font-semibold">Request Not Found</h2>
          <p className="text-muted-foreground mt-2">
            The request you are looking for does not exist.
          </p>
          <Button onClick={() => navigate(-1)} className="mt-6">
            Go Back
          </Button>
        </div>
      </Layout>
    );
  }

  const canApprove = user?.role.includes("approver") && request.status === "pending";
  const canSubmitReceipt =
    user?.role === "staff" &&
    request.created_by === user?.id &&
    request.status === "approved" &&
    !request.receipt;

  return (
    <Layout>
      <div className="space-y-8">
        <div>
          <Link
            to="/requests"
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to all requests
          </Link>
          <div className="flex flex-col md:flex-row md:items-start md:justify-between">
            <div>
              <h1 className="text-3xl font-bold">{request.title}</h1>
              <p className="text-muted-foreground mt-1">
                Request #{request.id.slice(0, 8)}
              </p>
            </div>
            <StatusBadge status={request.status} className="mt-2 md:mt-0" />
          </div>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          <div className="space-y-8 lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Details</CardTitle>
                <CardDescription>
                  A financial snapshot of the purchase request.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                  <InfoItem icon={DollarSign} label="Amount" value={`$${request.amount.toLocaleString()}`} />
                  <InfoItem icon={Calendar} label="Created" value={new Date(request.created_at).toLocaleDateString()} />
                  <InfoItem icon={User} label="Created By" value={request.created_by_name || "Unknown"} />
                </div>
                <Separator className="my-6" />
                <div>
                  <h3 className="font-semibold mb-2">Business Justification</h3>
                  <p className="text-muted-foreground">{request.description}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Documents</CardTitle>
                <CardDescription>
                  Attached files for this request.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {[
                  { label: "Proforma", href: request.proforma, icon: FileText },
                  { label: "Purchase Order", href: request.purchase_order, icon: Download },
                  { label: "Receipt", href: request.receipt, icon: FileText },
                ]
                  .filter((doc) => doc.href)
                  .map((doc) => (
                    <a
                      key={doc.label}
                      href={doc.href!}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group"
                    >
                      <div className="flex items-center gap-4 rounded-lg border p-4 transition-colors hover:bg-accent">
                        <doc.icon className="h-6 w-6 text-primary" />
                        <div>
                          <p className="font-semibold">{doc.label}</p>
                          <p className="text-xs text-muted-foreground">
                            Click to view
                          </p>
                        </div>
                      </div>
                    </a>
                  ))}
              </CardContent>
            </Card>
            
            {request.receipt_validation && (
              <Card>
                <CardHeader>
                  <CardTitle>Receipt Validation</CardTitle>
                  <CardDescription>
                    Automated checks against the purchase order.
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-2">
                  <Badge variant={request.receipt_validation.is_valid ? "default" : "destructive"}>
                    {request.receipt_validation.is_valid ? "Valid" : "Discrepancy Found"}
                  </Badge>
                  <Badge variant={request.receipt_validation.vendor_match ? "secondary" : "destructive"}>
                    Vendor: {request.receipt_validation.vendor_match ? "Match" : "Mismatch"}
                  </Badge>
                  <Badge variant={request.receipt_validation.price_match ? "secondary" : "destructive"}>
                    Amount: {request.receipt_validation.price_match ? "Match" : "Mismatch"}
                  </Badge>
                </CardContent>
              </Card>
            )}

            {canApprove && <ActionCard title="Approval Action" description="Review the request and make a decision." onAction={handleAction} loading={actionLoading} comment={comment} setComment={setComment} />}
            {canSubmitReceipt && <SubmitReceiptCard onSubmit={handleSubmitReceipt} loading={actionLoading} receipt={receipt} setReceipt={setReceipt} />}

          </div>

          <div className="space-y-8">
            <Card>
              <CardHeader>
                <CardTitle>Approval History</CardTitle>
                <CardDescription>
                  A complete log of all actions taken on this request.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {request.approvals.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No approvals have been logged yet.</p>
                ) : (
                  <div className="space-y-6">
                    {request.approvals.map((approval, index) => (
                      <div key={approval.id} className="flex gap-4">
                        <div className="flex flex-col items-center">
                          <div className={`h-8 w-8 rounded-full flex items-center justify-center bg-${approval.status === "approved" ? "green" : "red"}-100`}>
                            {approval.status === 'approved' ? <CheckCircle className="h-5 w-5 text-green-600" /> : <XCircle className="h-5 w-5 text-red-600" />}
                          </div>
                          {index !== request.approvals.length - 1 && <div className="w-px h-full bg-border" />}
                        </div>
                        <div className="flex-1">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-semibold">{approval.approver_name}</p>
                              <p className="text-xs text-muted-foreground">Level {approval.approver_level} Approver</p>
                            </div>
                            <p className="text-xs text-muted-foreground">{new Date(approval.created_at).toLocaleDateString()}</p>
                          </div>
                          {approval.comment && (
                            <div className="mt-2 text-sm text-muted-foreground bg-secondary p-3 rounded-lg border">
                              “{approval.comment}”
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  );
};

// Helper components for RequestDetail page

const InfoItem = ({ icon: Icon, label, value }: { icon: React.ElementType, label: string, value: string }) => (
  <div className="flex items-center gap-4">
    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary">
      <Icon className="h-5 w-5 text-muted-foreground" />
    </div>
    <div>
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="font-semibold">{value}</p>
    </div>
  </div>
);

const ActionCard = ({ title, description, onAction, loading, comment, setComment }: any) => (
  <Card>
    <CardHeader>
      <CardTitle>{title}</CardTitle>
      <CardDescription>{description}</CardDescription>
    </CardHeader>
    <CardContent className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="comment">Comment (optional)</Label>
        <Textarea
          id="comment"
          placeholder="Provide context for your decision..."
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={3}
        />
      </div>
      <div className="flex justify-end gap-4">
        <Button onClick={() => onAction('reject')} disabled={loading} variant="destructive">
          <XCircle className="mr-2 h-4 w-4" /> Reject
        </Button>
        <Button onClick={() => onAction('approve')} disabled={loading}>
          <CheckCircle className="mr-2 h-4 w-4" /> Approve
        </Button>
      </div>
    </CardContent>
  </Card>
);

const SubmitReceiptCard = ({ onSubmit, loading, receipt, setReceipt }: any) => (
  <Card>
    <CardHeader>
      <CardTitle>Submit Receipt</CardTitle>
      <CardDescription>Upload the receipt to finalize this request.</CardDescription>
    </CardHeader>
    <CardContent className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="receipt">Receipt Document</Label>
        <Input
          id="receipt"
          type="file"
          accept=".pdf,.png,.jpg,.jpeg"
          onChange={(e) => setReceipt(e.target.files?.[0] || null)}
        />
        {receipt && (
          <p className="text-sm text-muted-foreground">
            Selected: {receipt.name}
          </p>
        )}
      </div>
      <Button onClick={onSubmit} disabled={!receipt || loading} className="w-full">
        <Upload className="mr-2 h-4 w-4" />
        Submit Receipt
      </Button>
    </CardContent>
  </Card>
);

export default RequestDetail;
