import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Grid,
  Chip,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Phone as PhoneIcon,
  AccountBalance as AccountBalanceIcon,
  Payment as PaymentIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

interface PaymentMethod {
  id: string;
  name: string;
  type: string;
  provider: string;
  is_active: boolean;
  supported_currencies: string[];
  min_amount: number;
  max_amount: number;
  processing_fee_percent: number;
  processing_fee_fixed: number;
}

interface MobileMoneyPaymentProps {
  onSuccess?: (transactionId: string) => void;
  onError?: (error: string) => void;
  onClose?: () => void;
}

const MobileMoneyPayment: React.FC<MobileMoneyPaymentProps> = ({
  onSuccess,
  onError,
  onClose,
}) => {
  const [loading, setLoading] = useState(false);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  const [amount, setAmount] = useState<string>('');
  const [phoneNumber, setPhoneNumber] = useState<string>('');
  const [currency, setCurrency] = useState<string>('USD');
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [transactionId, setTransactionId] = useState<string>('');

  // Mock payment methods - in real app, fetch from API
  const mockPaymentMethods: PaymentMethod[] = [
    {
      id: 'momo_ghana',
      name: 'Mobile Money (Ghana)',
      type: 'mobile_money',
      provider: 'momo',
      is_active: true,
      supported_currencies: ['GHS'],
      min_amount: 1.0,
      max_amount: 5000.0,
      processing_fee_percent: 1.5,
      processing_fee_fixed: 0.1,
    },
    {
      id: 'momo_kenya',
      name: 'M-Pesa (Kenya)',
      type: 'mobile_money',
      provider: 'mpesa',
      is_active: true,
      supported_currencies: ['KES'],
      min_amount: 10.0,
      max_amount: 70000.0,
      processing_fee_percent: 1.0,
      processing_fee_fixed: 0.0,
    },
    {
      id: 'momo_nigeria',
      name: 'Paga (Nigeria)',
      type: 'mobile_money',
      provider: 'paga',
      is_active: true,
      supported_currencies: ['NGN'],
      min_amount: 100.0,
      max_amount: 100000.0,
      processing_fee_percent: 2.0,
      processing_fee_fixed: 0.0,
    },
  ];

  useEffect(() => {
    // Load payment methods
    setPaymentMethods(mockPaymentMethods);
  }, []);

  const handleMethodChange = (methodId: string) => {
    setSelectedMethod(methodId);
    const method = paymentMethods.find(m => m.id === methodId);
    if (method) {
      setCurrency(method.supported_currencies[0]);
    }
  };

  const calculateFees = () => {
    if (!selectedMethod || !amount) return { processingFee: 0, totalAmount: 0 };
    
    const method = paymentMethods.find(m => m.id === selectedMethod);
    if (!method) return { processingFee: 0, totalAmount: 0 };
    
    const amountNum = parseFloat(amount);
    const processingFee = (amountNum * method.processing_fee_percent / 100) + method.processing_fee_fixed;
    const totalAmount = amountNum + processingFee;
    
    return { processingFee, totalAmount };
  };

  const validateForm = () => {
    if (!selectedMethod) {
      setError('Please select a payment method');
      return false;
    }
    
    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a valid amount');
      return false;
    }
    
    if (!phoneNumber) {
      setError('Please enter your phone number');
      return false;
    }
    
    const method = paymentMethods.find(m => m.id === selectedMethod);
    if (method) {
      const amountNum = parseFloat(amount);
      if (amountNum < method.min_amount) {
        setError(`Minimum amount is ${method.min_amount} ${currency}`);
        return false;
      }
      if (amountNum > method.max_amount) {
        setError(`Maximum amount is ${method.max_amount} ${currency}`);
        return false;
      }
    }
    
    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;
    
    setLoading(true);
    setError('');
    
    try {
      // Mock API call - replace with actual API
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Generate transaction ID
      const newTransactionId = `txn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setTransactionId(newTransactionId);
      
      // Show confirmation dialog
      setShowConfirmation(true);
      
    } catch (err) {
      setError('Failed to process payment. Please try again.');
      onError?.('Payment processing failed');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmPayment = async () => {
    setLoading(true);
    
    try {
      // Mock API call to process mobile money payment
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      setSuccess('Payment processed successfully!');
      onSuccess?.(transactionId);
      
      // Close confirmation dialog
      setShowConfirmation(false);
      
    } catch (err) {
      setError('Payment failed. Please try again.');
      onError?.('Payment failed');
    } finally {
      setLoading(false);
    }
  };

  const { processingFee, totalAmount } = calculateFees();
  const selectedMethodData = paymentMethods.find(m => m.id === selectedMethod);

  return (
    <Box>
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <PaymentIcon sx={{ mr: 2, color: 'primary.main' }} />
            <Typography variant="h6">Mobile Money Payment</Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {success}
            </Alert>
          )}

          <Grid container spacing={3}>
            {/* Payment Method Selection */}
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Select Payment Method</InputLabel>
                <Select
                  value={selectedMethod}
                  onChange={(e) => handleMethodChange(e.target.value)}
                  label="Select Payment Method"
                >
                  {paymentMethods.map((method) => (
                    <MenuItem key={method.id} value={method.id}>
                      <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="body1">{method.name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {method.supported_currencies.join(', ')} • Fee: {method.processing_fee_percent}%
                          </Typography>
                        </Box>
                        <Chip
                          label={`${method.min_amount}-${method.max_amount}`}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Amount Input */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Amount"
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                InputProps={{
                  startAdornment: <Typography sx={{ mr: 1 }}>{currency}</Typography>,
                }}
                helperText={selectedMethodData ? 
                  `Min: ${selectedMethodData.min_amount} ${currency}, Max: ${selectedMethodData.max_amount} ${currency}` : 
                  ''
                }
              />
            </Grid>

            {/* Phone Number */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Phone Number"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="e.g., +233 24 123 4567"
                InputProps={{
                  startAdornment: <PhoneIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>

            {/* Fee Breakdown */}
            {selectedMethod && amount && (
              <Grid item xs={12}>
                <Card variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Fee Breakdown
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">Amount:</Typography>
                    <Typography variant="body2">{amount} {currency}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">Processing Fee:</Typography>
                    <Typography variant="body2">{processingFee.toFixed(2)} {currency}</Typography>
                  </Box>
                  <Divider sx={{ my: 1 }} />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body1" fontWeight="bold">Total:</Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {totalAmount.toFixed(2)} {currency}
                    </Typography>
                  </Box>
                </Card>
              </Grid>
            )}

            {/* Action Buttons */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  onClick={onClose}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  onClick={handleSubmit}
                  disabled={loading || !selectedMethod || !amount || !phoneNumber}
                  startIcon={loading ? <CircularProgress size={20} /> : <PaymentIcon />}
                >
                  {loading ? 'Processing...' : 'Process Payment'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <Dialog
        open={showConfirmation}
        onClose={() => setShowConfirmation(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Confirm Payment</Typography>
            <IconButton onClick={() => setShowConfirmation(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 3 }}>
            <Typography variant="body1" gutterBottom>
              Please confirm your payment details:
            </Typography>
            
            <Card variant="outlined" sx={{ p: 2, mt: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Payment Method:</Typography>
                <Typography variant="body2">{selectedMethodData?.name}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Phone Number:</Typography>
                <Typography variant="body2">{phoneNumber}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Amount:</Typography>
                <Typography variant="body2">{amount} {currency}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Processing Fee:</Typography>
                <Typography variant="body2">{processingFee.toFixed(2)} {currency}</Typography>
              </Box>
              <Divider sx={{ my: 1 }} />
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body1" fontWeight="bold">Total:</Typography>
                <Typography variant="body1" fontWeight="bold">
                  {totalAmount.toFixed(2)} {currency}
                </Typography>
              </Box>
            </Card>
            
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                You will receive a payment prompt on your phone. Please complete the payment to add funds to your wallet.
              </Typography>
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setShowConfirmation(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleConfirmPayment}
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <CheckCircleIcon />}
          >
            {loading ? 'Processing...' : 'Confirm Payment'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MobileMoneyPayment; 