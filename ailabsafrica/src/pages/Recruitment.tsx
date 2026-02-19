import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import {
  Users,
  Rocket,
  Heart,
  Zap,
  Globe,
  TrendingUp,
  Shield,
  Award,
  Coffee,
  Laptop,
  DollarSign,
  GraduationCap,
  Send,
  MapPin,
  Briefcase,
  Clock
} from 'lucide-react';
import { Link } from 'react-router-dom';
import MetaTags from '@/components/SEO/MetaTags';

/**
 * Job position interface defining job listing structure
 */
interface JobPosition {
  id: string;
  title: string;
  department: string;
  location: string;
  type: string; // Full-time / Part-time
  description: string;
}

/**
 * Recruitment page component
 * Displays company culture, job openings, and application form
 */
const Recruitment = () => {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState<string>('');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    position: '',
    linkedin: '',
    portfolio: '',
    coverLetter: '',
    resume: null as File | null
  });

  /**
   * Available job positions at AI Labs Africa
   */
  const jobPositions: JobPosition[] = [
    {
      id: 'ml-engineer',
      title: 'Machine Learning Engineer',
      department: 'Engineering',
      location: 'Accra, Ghana (Hybrid)',
      type: 'Full-time / Part-time',
      description: 'Build and deploy cutting-edge ML models for African languages and contexts. Work with NLP, speech recognition, and conversational AI.'
    },
    {
      id: 'fullstack-dev',
      title: 'Full Stack Developer',
      department: 'Engineering',
      location: 'Accra, Ghana (Hybrid)',
      type: 'Full-time / Part-time',
      description: 'Develop scalable web applications using React, TypeScript, Python, and FastAPI. Build features for our KasaAI platform.'
    },
    {
      id: 'ai-researcher',
      title: 'AI Research Scientist',
      department: 'Research',
      location: 'Remote',
      type: 'Full-time / Part-time',
      description: 'Conduct research in multilingual NLP, speech synthesis, and conversational AI specifically for African languages and use cases.'
    },
    {
      id: 'product-manager',
      title: 'Product Manager',
      department: 'Product',
      location: 'Accra, Ghana (Hybrid)',
      type: 'Full-time / Part-time',
      description: 'Drive product strategy and roadmap for KasaAI. Work closely with engineering, design, and customers to build impactful AI solutions.'
    },
    {
      id: 'sales-exec',
      title: 'Sales Executive',
      department: 'Sales',
      location: 'Accra, Ghana',
      type: 'Full-time / Part-time',
      description: 'Drive business growth by identifying and closing deals with enterprises across Africa. Build relationships with key decision makers.'
    },
    {
      id: 'customer-success',
      title: 'Customer Success Manager',
      department: 'Customer Success',
      location: 'Accra, Ghana (Hybrid)',
      type: 'Full-time / Part-time',
      description: 'Ensure customer satisfaction and success with KasaAI. Provide technical support, training, and strategic guidance to clients.'
    },
    {
      id: 'sales-marketing-lead',
      title: 'Sales and Marketing Team Lead',
      department: 'Sales & Marketing',
      location: 'Remote',
      type: 'Full-time / Part-time',
      description: 'Lead and grow our sales and marketing team. Develop GTM strategies, drive revenue growth, and build brand awareness across Africa. Own the full sales cycle and marketing funnel.'
    }
  ];

  /**
   * Company benefits offered to employees
   */
  const benefits = [
    {
      icon: DollarSign,
      title: 'Competitive Salary',
      description: 'Market-leading compensation with equity options for full-time roles'
    },
    {
      icon: Laptop,
      title: 'Remote-Friendly',
      description: 'Flexible work arrangements with hybrid and remote options'
    },
    {
      icon: GraduationCap,
      title: 'Learning & Development',
      description: 'Annual learning budget for courses, conferences, and certifications'
    },
    {
      icon: Heart,
      title: 'Health Insurance',
      description: 'Comprehensive health coverage for you and your family'
    },
    {
      icon: Coffee,
      title: 'Work-Life Balance',
      description: 'Flexible hours, unlimited PTO, and mental health support'
    },
    {
      icon: Award,
      title: 'Career Growth',
      description: 'Clear career progression paths with regular feedback and mentorship'
    }
  ];

  /**
   * Company values that guide our work
   */
  const values = [
    {
      icon: Rocket,
      title: 'Innovation First',
      description: 'We push boundaries and embrace new technologies to solve hard problems'
    },
    {
      icon: Users,
      title: 'African Focus',
      description: 'Built by Africans, for Africa. We understand local contexts and needs'
    },
    {
      icon: Globe,
      title: 'Global Impact',
      description: 'Local solutions with global ambitions. We aim to scale across continents'
    },
    {
      icon: Shield,
      title: 'Ethics & Trust',
      description: 'We build AI responsibly with transparency, privacy, and fairness at the core'
    }
  ];

  /**
   * Handle application form submission
   * Sends application data to backend API
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Validate required fields
      if (!formData.name || !formData.email || !formData.position || !formData.phone || !formData.coverLetter) {
        throw new Error('Please fill in all required fields');
      }

      // Validate resume if provided
      if (formData.resume && formData.resume.size > 5 * 1024 * 1024) {
        throw new Error('Resume file too large. Maximum size is 5MB.');
      }

      // Create FormData for multipart/form-data submission
      const submitData = new FormData();
      submitData.append('name', formData.name);
      submitData.append('email', formData.email);
      submitData.append('phone', formData.phone);
      submitData.append('position', formData.position);
      submitData.append('cover_letter', formData.coverLetter);

      if (formData.linkedin) {
        submitData.append('linkedin', formData.linkedin);
      }
      if (formData.portfolio) {
        submitData.append('portfolio', formData.portfolio);
      }
      if (formData.resume) {
        submitData.append('resume', formData.resume);
      }

      // Submit to backend API
      const apiUrl = import.meta.env.VITE_API_URL || 'https://api.ailabsafrica.com';
      const response = await fetch(`${apiUrl}/api/recruitment/apply`, {
        method: 'POST',
        body: submitData
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.detail || result.error || 'Failed to submit application');
      }

      toast({
        title: "Application submitted successfully!",
        description: result.message || "We'll review your application and get back to you within 5 business days.",
      });

      // Reset form
      setFormData({
        name: '',
        email: '',
        phone: '',
        position: '',
        linkedin: '',
        portfolio: '',
        coverLetter: '',
        resume: null
      });
      setSelectedPosition('');

      // Reset file input
      const fileInput = document.getElementById('resume') as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }

    } catch (error: any) {
      console.error('Application submission error:', error);
      toast({
        title: "Error submitting application",
        description: error.message || "Please email your application directly to careers@ailabsafrica.com",
        variant: "destructive"
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Handle form input changes
   */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  /**
   * Handle file input change for resume upload
   */
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setFormData(prev => ({
      ...prev,
      resume: file
    }));
  };

  return (
    <>
      <MetaTags
        title="Careers - AI Labs Africa"
        description="Join AI Labs Africa and help build the future of AI in Africa. View open positions and apply today."
      />
      <div className="min-h-screen bg-background">
        {/* Hero Section */}
        <section className="py-20 bg-gradient-to-r from-tech-blue to-tech-blue-light text-white">
          <div className="container text-center">
            <h1 className="text-5xl md:text-6xl font-bold mb-6">
              Join Us in Building the Future of AI in Africa
            </h1>
            <p className="text-xl md:text-2xl text-white/90 max-w-3xl mx-auto mb-8">
              We're a team of passionate innovators creating AI solutions that transform businesses and communities across Africa. Come build the future with us.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" variant="secondary" asChild>
                <a href="#positions" className="bg-african-gold hover:bg-african-gold-dark text-black">
                  View Open Positions
                </a>
              </Button>
              <Button size="lg" variant="outline" asChild className="border-white/30 text-white hover:bg-white/10">
                <a href="#apply">Apply Now</a>
              </Button>
            </div>
          </div>
        </section>

        {/* Company Values */}
        <section className="py-20 bg-background">
          <div className="container">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-tech-blue to-african-gold bg-clip-text text-transparent">
                Our Values
              </h2>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
                The principles that guide everything we do
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              {values.map((value, index) => {
                const Icon = value.icon;
                return (
                  <Card key={index} className="text-center border-0 shadow-lg hover:shadow-xl transition-all duration-300">
                    <CardHeader>
                      <div className="w-14 h-14 bg-gradient-to-br from-tech-blue to-african-gold rounded-lg flex items-center justify-center mx-auto mb-4">
                        <Icon className="h-7 w-7 text-white" />
                      </div>
                      <CardTitle>{value.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CardDescription>{value.description}</CardDescription>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        </section>

        {/* Why Work With Us */}
        <section className="py-20 bg-muted/30">
          <div className="container">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4">Why AI Labs Africa?</h2>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
                Work on cutting-edge AI technology while making a real impact across Africa
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <TrendingUp className="h-8 w-8 text-tech-blue mb-2" />
                  <CardTitle>Rapid Growth</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>
                    Join a fast-growing startup backed by leading investors. Experience exponential professional growth as we scale.
                  </CardDescription>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <Zap className="h-8 w-8 text-african-gold mb-2" />
                  <CardTitle>Cutting-Edge Tech</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>
                    Work with the latest AI technologies, from large language models to speech synthesis and conversational AI.
                  </CardDescription>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <Heart className="h-8 w-8 text-red-500 mb-2" />
                  <CardTitle>Make an Impact</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>
                    Your work directly impacts millions of people across Africa, improving access to services and economic opportunities.
                  </CardDescription>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <Users className="h-8 w-8 text-tech-blue mb-2" />
                  <CardTitle>Diverse Team</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>
                    Work with talented individuals from across Africa and beyond, bringing diverse perspectives and experiences.
                  </CardDescription>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <Rocket className="h-8 w-8 text-african-gold mb-2" />
                  <CardTitle>Ownership</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>
                    Take ownership of projects from day one. Your ideas and contributions shape our products and direction.
                  </CardDescription>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <Globe className="h-8 w-8 text-green-500 mb-2" />
                  <CardTitle>Global Reach</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>
                    While we focus on Africa, our technology and ambitions are global. Build solutions that scale worldwide.
                  </CardDescription>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* Benefits */}
        <section className="py-20 bg-background">
          <div className="container">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4">Benefits & Perks</h2>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
                We invest in our team's wellbeing and growth
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {benefits.map((benefit, index) => {
                const Icon = benefit.icon;
                return (
                  <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-all duration-300">
                    <CardHeader>
                      <div className="flex items-center space-x-3 mb-2">
                        <div className="w-10 h-10 bg-gradient-to-br from-tech-blue to-african-gold rounded-lg flex items-center justify-center">
                          <Icon className="h-5 w-5 text-white" />
                        </div>
                        <CardTitle className="text-lg">{benefit.title}</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <CardDescription>{benefit.description}</CardDescription>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        </section>

        {/* Open Positions */}
        <section id="positions" className="py-20 bg-muted/30">
          <div className="container">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4">Open Positions</h2>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
                Find your next opportunity and help shape the future of AI in Africa
              </p>
            </div>

            <div className="space-y-6 max-w-5xl mx-auto">
              {jobPositions.map((job) => (
                <Card key={job.id} className="border-0 shadow-lg hover:shadow-xl transition-all duration-300">
                  <CardContent className="p-6">
                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                      <div className="flex-1">
                        <h3 className="text-2xl font-bold mb-2">{job.title}</h3>
                        <div className="flex flex-wrap gap-3 mb-3">
                          <span className="flex items-center text-sm text-muted-foreground">
                            <Briefcase className="h-4 w-4 mr-1" />
                            {job.department}
                          </span>
                          <span className="flex items-center text-sm text-muted-foreground">
                            <MapPin className="h-4 w-4 mr-1" />
                            {job.location}
                          </span>
                          <span className="flex items-center text-sm text-muted-foreground">
                            <Clock className="h-4 w-4 mr-1" />
                            {job.type}
                          </span>
                        </div>
                        <p className="text-muted-foreground">{job.description}</p>
                      </div>
                      <div className="lg:ml-6">
                        <Button
                          onClick={() => {
                            setSelectedPosition(job.title);
                            setFormData(prev => ({ ...prev, position: job.title }));
                            document.getElementById('apply')?.scrollIntoView({ behavior: 'smooth' });
                          }}
                          className="w-full lg:w-auto"
                        >
                          Apply Now
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="text-center mt-12">
              <p className="text-muted-foreground mb-4">
                Don't see a position that fits? We're always looking for exceptional talent.
              </p>
              <Button variant="outline" onClick={() => {
                setSelectedPosition('General Application');
                setFormData(prev => ({ ...prev, position: 'General Application' }));
                document.getElementById('apply')?.scrollIntoView({ behavior: 'smooth' });
              }}>
                Submit General Application
              </Button>
            </div>
          </div>
        </section>

        {/* Application Form */}
        <section id="apply" className="py-20 bg-background">
          <div className="container">
            <div className="max-w-3xl mx-auto">
              <Card className="border-0 shadow-xl">
                <CardHeader className="text-center">
                  <CardTitle className="text-3xl">Apply Now</CardTitle>
                  <CardDescription>
                    {selectedPosition ? `Applying for: ${selectedPosition}` : 'Submit your application and join our team'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <Label htmlFor="name">Full Name *</Label>
                        <Input
                          id="name"
                          name="name"
                          value={formData.name}
                          onChange={handleChange}
                          required
                          placeholder="Your full name"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email">Email Address *</Label>
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          value={formData.email}
                          onChange={handleChange}
                          required
                          placeholder="your.email@example.com"
                        />
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <Label htmlFor="phone">Phone Number *</Label>
                        <Input
                          id="phone"
                          name="phone"
                          type="tel"
                          value={formData.phone}
                          onChange={handleChange}
                          required
                          placeholder="+233 XX XXX XXXX"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="position">Position *</Label>
                        <select
                          id="position"
                          name="position"
                          value={formData.position}
                          onChange={handleChange}
                          required
                          className="w-full h-10 px-3 py-2 text-sm bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                        >
                          <option value="">Select a position</option>
                          {jobPositions.map(job => (
                            <option key={job.id} value={job.title}>{job.title}</option>
                          ))}
                          <option value="General Application">General Application</option>
                        </select>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <Label htmlFor="linkedin">LinkedIn Profile</Label>
                        <Input
                          id="linkedin"
                          name="linkedin"
                          type="url"
                          value={formData.linkedin}
                          onChange={handleChange}
                          placeholder="https://linkedin.com/in/yourprofile"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="portfolio">Portfolio/Website</Label>
                        <Input
                          id="portfolio"
                          name="portfolio"
                          type="url"
                          value={formData.portfolio}
                          onChange={handleChange}
                          placeholder="https://yourportfolio.com"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="resume">Resume/CV *</Label>
                      <Input
                        id="resume"
                        name="resume"
                        type="file"
                        onChange={handleFileChange}
                        accept=".pdf,.doc,.docx"
                        required
                        className="cursor-pointer"
                      />
                      <p className="text-xs text-muted-foreground">
                        Accepted formats: PDF, DOC, DOCX (Max 5MB)
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="coverLetter">Cover Letter *</Label>
                      <Textarea
                        id="coverLetter"
                        name="coverLetter"
                        value={formData.coverLetter}
                        onChange={handleChange}
                        required
                        rows={8}
                        placeholder="Tell us about yourself, your experience, and why you want to join AI Labs Africa..."
                      />
                    </div>

                    <Button
                      type="submit"
                      size="lg"
                      className="w-full"
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? (
                        <>Submitting Application...</>
                      ) : (
                        <>
                          Submit Application
                          <Send className="ml-2 h-4 w-4" />
                        </>
                      )}
                    </Button>

                    <p className="text-center text-sm text-muted-foreground">
                      By submitting this application, you agree to our privacy policy and data processing terms.
                    </p>
                  </form>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 bg-gradient-to-r from-tech-blue to-african-gold text-white">
          <div className="container text-center">
            <h2 className="text-4xl font-bold mb-6">Questions About Working With Us?</h2>
            <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
              We'd love to hear from you. Reach out to our team to learn more about opportunities at AI Labs Africa.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" variant="secondary" asChild>
                <Link to="/contact" className="bg-white hover:bg-white/90 text-tech-blue">
                  Contact Us
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild className="border-white/30 text-white hover:bg-white/10">
                <Link to="/demos">Explore Our Products</Link>
              </Button>
            </div>
          </div>
        </section>
      </div>
    </>
  );
};

export default Recruitment;
