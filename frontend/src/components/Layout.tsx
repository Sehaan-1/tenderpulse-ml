import { useState, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  AppBar,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery
} from "@mui/material";
import { alpha, type PaletteMode, useTheme } from "@mui/material/styles";
import AnalyticsIcon from "@mui/icons-material/QueryStats";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import DashboardIcon from "@mui/icons-material/Dashboard";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import MenuIcon from "@mui/icons-material/Menu";
import TableRowsIcon from "@mui/icons-material/TableRows";
import UploadFileIcon from "@mui/icons-material/UploadFile";

interface LayoutProps {
  children: ReactNode;
  mode: PaletteMode;
  onToggleMode: () => void;
}

const navItems = [
  { label: "Dashboard", path: "/", icon: <DashboardIcon /> },
  { label: "Tenders", path: "/tenders", icon: <TableRowsIcon /> },
  { label: "Classify", path: "/classify", icon: <UploadFileIcon /> },
  { label: "Analytics", path: "/analytics", icon: <AnalyticsIcon /> }
];

export default function Layout({ children, mode, onToggleMode }: LayoutProps) {
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up("md"));
  const [expanded, setExpanded] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const drawerWidth = expanded ? 252 : 76;

  const drawerContent = (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <Toolbar sx={{ gap: 1.5, minHeight: 68 }}>
        <Box
          sx={{
            width: 34,
            height: 34,
            borderRadius: 1.5,
            display: "grid",
            placeItems: "center",
            color: "#FFFFFF",
            bgcolor: "primary.main",
            fontWeight: 800
          }}
        >
          TP
        </Box>
        {expanded && (
          <Box>
            <Typography variant="subtitle1" fontWeight={800} lineHeight={1.1}>
              TenderPulse
            </Typography>
            <Typography variant="caption" color="text.secondary">
              ML Dashboard
            </Typography>
          </Box>
        )}
      </Toolbar>
      <Divider />
      <List sx={{ px: 1.25, py: 1.5, flexGrow: 1 }}>
        {navItems.map((item) => {
          const selected = location.pathname === item.path;
          return (
            <Tooltip key={item.path} title={expanded ? "" : item.label} placement="right">
              <ListItemButton
                component={NavLink}
                to={item.path}
                selected={selected}
                onClick={() => setMobileOpen(false)}
                sx={{
                  minHeight: 44,
                  justifyContent: expanded ? "initial" : "center",
                  px: expanded ? 1.5 : 1,
                  mb: 0.5,
                  borderRadius: 1,
                  "&.Mui-selected": {
                    color: "primary.main",
                    bgcolor: alpha(theme.palette.primary.main, 0.14)
                  },
                  "&.Mui-selected:hover": {
                    bgcolor: alpha(theme.palette.primary.main, 0.2)
                  }
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: expanded ? 38 : 0,
                    color: "inherit",
                    justifyContent: "center"
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                {expanded && <ListItemText primary={item.label} />}
              </ListItemButton>
            </Tooltip>
          );
        })}
      </List>
      {isDesktop && (
        <Box sx={{ p: 1.25 }}>
          <Tooltip title={expanded ? "Collapse sidebar" : "Expand sidebar"} placement="right">
            <IconButton
              onClick={() => setExpanded((value) => !value)}
              sx={{ width: 44, height: 44 }}
              aria-label={expanded ? "Collapse sidebar" : "Expand sidebar"}
            >
              {expanded ? <ChevronLeftIcon /> : <ChevronRightIcon />}
            </IconButton>
          </Tooltip>
        </Box>
      )}
    </Box>
  );

  return (
    <Box sx={{ minHeight: "100vh", display: "flex", bgcolor: "background.default" }}>
      <AppBar
        position="fixed"
        color="transparent"
        elevation={0}
        sx={{
          backdropFilter: "blur(12px)",
          borderBottom: 1,
          borderColor: "divider",
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` }
        }}
      >
        <Toolbar sx={{ minHeight: 68, gap: 1.5 }}>
          {!isDesktop && (
            <IconButton onClick={() => setMobileOpen(true)} aria-label="Open navigation">
              <MenuIcon />
            </IconButton>
          )}
          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
            <Typography variant="h6" noWrap>
              TenderPulse ML
            </Typography>
          </Box>
          <Tooltip title={mode === "dark" ? "Switch to light mode" : "Switch to dark mode"}>
            <IconButton onClick={onToggleMode} aria-label="Toggle color mode">
              {mode === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}>
        <Drawer
          variant={isDesktop ? "permanent" : "temporary"}
          open={isDesktop || mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          PaperProps={{
            sx: {
              width: isDesktop ? drawerWidth : 252,
              bgcolor: "background.paper",
              borderRight: 1,
              borderColor: "divider",
              overflowX: "hidden",
              transition: theme.transitions.create("width", {
                duration: theme.transitions.duration.shortest
              })
            }
          }}
        >
          {drawerContent}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          minWidth: 0,
          px: { xs: 2, sm: 2.5, lg: 3 },
          pb: 4,
          pt: "92px"
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
