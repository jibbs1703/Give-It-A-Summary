import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Avatar,
  Divider,
  Fab,
  Button,
  Card,
  CardContent,
  Grid,
  Alert,
  Chip,
} from '@mui/material';
import {
  Send as SendIcon,
  AttachFile as AttachFileIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Description as DescriptionIcon,
  Email as EmailIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as LoadingIcon,
} from '@mui/icons-material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function LandingPage({ onStartChat }) {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <Container maxWidth="lg">
        <Paper
          elevation={10}
          sx={{
            p: 4,
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            borderRadius: 3,
          }}
        >
          <Box textAlign="center" mb={4}>
            <Typography
              variant="h2"
              component="h1"
              sx={{
                fontWeight: 'bold',
                color: 'primary.main',
                mb: 2,
              }}
            >
              📄 Give-It-A-Summary
            </Typography>
            <Typography
              variant="h5"
              sx={{
                color: 'text.secondary',
                mb: 3,
              }}
            >
              Your AI-Powered Academic Paper Summarization Assistant
            </Typography>
            <Typography variant="body1" sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}>
              Tired of drowning in academic papers? Let our AI agent read through complex research articles
              and deliver clear, concise summaries directly to your email. Just chat with our intelligent
              assistant, upload your paper, and specify your needs!
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={onStartChat}
              sx={{
                px: 4,
                py: 1.5,
                fontSize: '1.1rem',
                borderRadius: 2,
                boxShadow: 3,
                '&:hover': {
                  boxShadow: 6,
                },
              }}
            >
              Start Chatting with AI Assistant
            </Button>
          </Box>

          <Grid container spacing={3} sx={{ mt: 4 }}>
            <Grid item xs={12} md={4}>
              <Card sx={{ height: '100%', textAlign: 'center' }}>
                <CardContent>
                  <DescriptionIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Multiple Formats
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Supports PDF, DOCX, TXT, XLSX, and CSV files. Extract text from any academic document.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ height: '100%', textAlign: 'center' }}>
                <CardContent>
                  <SpeedIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Instant Summaries
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Get professional summaries in minutes, not hours. Customize length and style.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ height: '100%', textAlign: 'center' }}>
                <CardContent>
                  <EmailIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Email Delivery
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Receive beautifully formatted Word documents directly in your inbox.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Box textAlign="center" mt={4}>
            <Typography variant="h6" gutterBottom>
              How It Works
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircleIcon color="primary" />
                <Typography>1. Chat with AI assistant</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircleIcon color="primary" />
                <Typography>2. Upload your paper</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircleIcon color="primary" />
                <Typography>3. Specify summary needs</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircleIcon color="primary" />
                <Typography>4. Receive via email</Typography>
              </Box>
            </Box>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
}

function ChatInterface() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm your AI summarization assistant. Upload a paper and tell me what you need summarized!",
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [file, setFile] = useState(null);
  const [agentReady, setAgentReady] = useState(false);
  const [agentStatus, setAgentStatus] = useState('checking');
  const fileInputRef = useRef(null);

  // API base URL - use environment variable or default
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';

  // Check agent readiness on component mount
  useEffect(() => {
    checkAgentReadiness();
  }, []);

  const checkAgentReadiness = async () => {
    try {
      setAgentStatus('checking');
      const response = await fetch('/api/v1/health');
      const data = await response.json();

      if (response.ok && data['Backend Status'] === 'healthy') {
        setAgentReady(true);
        setAgentStatus('ready');
      } else {
        setAgentReady(false);
        setAgentStatus('unavailable');
      }
    } catch (error) {
      console.error('Failed to check agent readiness:', error);
      setAgentReady(false);
      setAgentStatus('error');
    }
  };

  const handleSend = async () => {
    if (!input.trim() && !file) return;

    const userMessage = {
      id: messages.length + 1,
      text: input,
      file: file,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    const currentFile = file;
    setInput('');
    setFile(null);

    try {
      // Prepare form data for the API call
      const formData = new FormData();
      formData.append('message', currentInput);

      if (currentFile) {
        formData.append('file', currentFile);
      }

      // Call the backend API
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      // Add the bot response
      const botResponse = {
        id: messages.length + 2,
        text: data.message || (data.success ? 'Request processed successfully!' : 'An error occurred while processing your request.'),
        sender: 'bot',
        timestamp: new Date(),
        success: data.success,
      };

      setMessages(prev => [...prev, botResponse]);

    } catch (error) {
      console.error('Failed to send message:', error);

      // Add error response
      const errorResponse = {
        id: messages.length + 2,
        text: 'Sorry, I encountered an error while processing your request. Please try again.',
        sender: 'bot',
        timestamp: new Date(),
        success: false,
      };

      setMessages(prev => [...prev, errorResponse]);
    }
  };

  const handleResend = async (messageToResend) => {
    // Set the input and file to the message being resent
    setInput(messageToResend.text);
    if (messageToResend.file) {
      setFile(messageToResend.file);
    }

    // Automatically send the message
    setTimeout(() => {
      handleSend();
    }, 100);
  };

  const handleFileSelect = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(10px)',
          padding: 2,
          boxShadow: 1,
        }}
      >
        <Container maxWidth="md">
          <Typography
            variant="h4"
            component="h1"
            sx={{
              textAlign: 'center',
              fontWeight: 'bold',
              color: 'primary.main',
            }}
          >
            📄 Give-It-A-Summary Chat
          </Typography>
          <Typography
            variant="subtitle1"
            sx={{
              textAlign: 'center',
              color: 'text.secondary',
              mt: 1,
            }}
          >
            Chat with your AI summarization assistant
          </Typography>
        </Container>
      </Box>

      {/* Agent Status Indicator */}
      <Container maxWidth="md" sx={{ py: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <Chip
            icon={
              agentStatus === 'ready' ? <CheckCircleIcon /> :
              agentStatus === 'checking' ? <LoadingIcon /> :
              <ErrorIcon />
            }
            label={
              agentStatus === 'ready' ? 'Agent is ready' :
              agentStatus === 'checking' ? 'Checking agent status...' :
              agentStatus === 'unavailable' ? 'Agent unavailable' :
              'Connection error'
            }
            color={
              agentStatus === 'ready' ? 'success' :
              agentStatus === 'checking' ? 'warning' :
              'error'
            }
            variant="outlined"
            sx={{
              fontWeight: 'bold',
              '& .MuiChip-icon': {
                animation: agentStatus === 'checking' ? 'spin 2s linear infinite' : 'none',
              },
            }}
          />
        </Box>
      </Container>

      {/* Chat Container */}
      <Container maxWidth="md" sx={{ flex: 1, py: 2 }}>
        <Paper
          elevation={3}
          sx={{
            height: '70vh',
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
          }}
        >
          {/* Messages */}
          <Box sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
            <List>
              {messages.map((message) => (
                <React.Fragment key={message.id}>
                  <ListItem
                    sx={{
                      justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        maxWidth: '70%',
                        flexDirection: message.sender === 'user' ? 'row-reverse' : 'row',
                      }}
                    >
                      <Avatar
                        sx={{
                          bgcolor: message.sender === 'user' ? 'primary.main' : 'secondary.main',
                          mx: 1,
                        }}
                      >
                        {message.sender === 'user' ? <PersonIcon /> : <BotIcon />}
                      </Avatar>
                      <Paper
                        elevation={1}
                        sx={{
                          p: 2,
                          backgroundColor: message.sender === 'user' ? 'primary.main' : 'grey.100',
                          color: message.sender === 'user' ? 'white' : 'text.primary',
                          borderRadius: 2,
                          position: 'relative',
                          '&:hover .resend-button': {
                            opacity: 1,
                          },
                        }}
                      >
                        <ListItemText
                          primary={message.text}
                          secondary={
                            message.file ? `📎 ${message.file.name}` : null
                          }
                        />
                        <Typography variant="caption" sx={{ opacity: 0.7 }}>
                          {message.timestamp.toLocaleTimeString()}
                        </Typography>
                        {message.sender === 'user' && (
                          <IconButton
                            size="small"
                            onClick={() => handleResend(message)}
                            className="resend-button"
                            sx={{
                              position: 'absolute',
                              top: 8,
                              right: 8,
                              opacity: 0,
                              transition: 'opacity 0.2s',
                              color: 'inherit',
                              '&:hover': {
                                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                              },
                            }}
                            title="Resend message"
                          >
                            ↻
                          </IconButton>
                        )}
                      </Paper>
                    </Box>
                  </ListItem>
                  <Divider variant="inset" component="li" />
                </React.Fragment>
              ))}
            </List>
          </Box>

          {/* Input Area */}
          <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
            {file && (
              <Box sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
                <Typography variant="body2" sx={{ mr: 1 }}>
                  📎 {file.name}
                </Typography>
                <IconButton size="small" onClick={() => setFile(null)}>
                  ✕
                </IconButton>
              </Box>
            )}
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Type your message... (e.g., 'Summarize this paper in 500 words')"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                sx={{ mr: 1 }}
              />
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                style={{ display: 'none' }}
                accept=".pdf,.docx,.txt,.xlsx,.xls,.csv"
              />
              <IconButton
                color="primary"
                onClick={() => fileInputRef.current.click()}
                sx={{ mr: 1 }}
              >
                <AttachFileIcon />
              </IconButton>
              <Fab color="primary" size="medium" onClick={handleSend}>
                <SendIcon />
              </Fab>
            </Box>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
}

function App() {
  const [showChat, setShowChat] = useState(false);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {showChat ? (
        <ChatInterface />
      ) : (
        <LandingPage onStartChat={() => setShowChat(true)} />
      )}
    </ThemeProvider>
  );
}

export default App;
