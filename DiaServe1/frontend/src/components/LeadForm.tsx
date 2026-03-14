import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";
import { User, Phone, CheckCircle2, Mail } from "lucide-react";
import { submitLead } from "@/lib/api/lead-api";

interface LeadFormProps {
    propertyId?: string;
    propertyName?: string;
}

export function LeadForm({ propertyId, propertyName }: LeadFormProps) {
    const [name, setName] = useState("");
    const [phone, setPhone] = useState("");
    const [email, setEmail] = useState("");
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const { toast } = useToast();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!propertyId) {
            toast({
                title: "Error",
                description: "Property information is missing. Please refresh the page.",
                variant: "destructive",
            });
            return;
        }
        setIsLoading(true);

        try {
            await submitLead({
                name,
                email,
                phone: phone || undefined,
                property_id: propertyId,
            });

            setIsSubmitted(true);
            toast({
                title: "Thank you!",
                description: "We've received your details and will contact you shortly.",
            });
        } catch (err) {
            toast({
                title: "Submission failed",
                description: err instanceof Error ? err.message : "Please try again later.",
                variant: "destructive",
            });
        } finally {
            setIsLoading(false);
        }
    };

    if (isSubmitted) {
        return (
            <Card className="border-success/20 bg-success/5 animate-scale-in">
                <CardContent className="p-12 text-center space-y-4">
                    <div className="mx-auto w-16 h-16 bg-success/20 rounded-full flex items-center justify-center">
                        <CheckCircle2 className="w-8 h-8 text-success" />
                    </div>
                    <h3 className="text-xl font-bold">Successfully Registered!</h3>
                    <p className="text-muted-foreground">
                        A representative will call you soon at <span className="font-semibold text-foreground">{phone}</span> or email you at <span className="font-semibold text-foreground">{email}</span> to discuss your interest in
                        <span className="font-semibold text-foreground"> {propertyName || 'our properties'}</span>.
                    </p>
                    <Button variant="outline" onClick={() => setIsSubmitted(false)}>Submit another query</Button>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="border-primary/10 shadow-lg">
            <CardHeader>
                <CardTitle className="text-xl">Interested in {propertyName || 'this property'}?</CardTitle>
                <CardDescription>
                    Leave your details and we'll get back to you with more information.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="lead-name">Full Name</Label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                id="lead-name"
                                placeholder="John Doe"
                                className="pl-10"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="lead-email">Email Address</Label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                id="lead-email"
                                type="email"
                                placeholder="john@example.com"
                                className="pl-10"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="lead-phone">Phone Number</Label>
                        <div className="relative">
                            <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                id="lead-phone"
                                type="tel"
                                placeholder="+233 XX XXX XXXX"
                                className="pl-10"
                                value={phone}
                                onChange={(e) => setPhone(e.target.value)}
                                required
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <Button type="submit" className="w-full" variant="gradient" disabled={isLoading}>
                        {isLoading ? "Submitting..." : "Contact Me About This"}
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}
