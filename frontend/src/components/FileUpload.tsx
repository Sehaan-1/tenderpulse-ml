import { ChangeEvent, DragEvent, useRef, useState } from "react";
import { Box, Button, Chip, Paper, Stack, Typography } from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import AttachFileIcon from "@mui/icons-material/AttachFile";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";

interface FileUploadProps {
  file: File | null;
  disabled?: boolean;
  onFile: (file: File) => void;
}

export default function FileUpload({ file, disabled = false, onFile }: FileUploadProps) {
  const theme = useTheme();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = (nextFile?: File) => {
    if (nextFile) {
      onFile(nextFile);
    }
  };

  const handleInput = (event: ChangeEvent<HTMLInputElement>) => {
    handleFile(event.target.files?.[0]);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    if (!disabled) {
      handleFile(event.dataTransfer.files?.[0]);
    }
  };

  return (
    <Paper
      variant="outlined"
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      sx={{
        p: { xs: 2.5, sm: 3 },
        borderStyle: "dashed",
        borderColor: dragging ? "primary.main" : "divider",
        bgcolor: dragging ? alpha(theme.palette.primary.main, 0.1) : "background.paper"
      }}
    >
      <Stack spacing={2} alignItems="flex-start">
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: 1.5,
            display: "grid",
            placeItems: "center",
            color: "primary.main",
            bgcolor: alpha(theme.palette.primary.main, 0.14)
          }}
        >
          <CloudUploadIcon />
        </Box>
        <Box>
          <Typography variant="h6">JSONL Upload</Typography>
          <Typography variant="body2" color="text.secondary">
            One tender record per line.
          </Typography>
        </Box>
        <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap" useFlexGap>
          <Button
            variant="contained"
            startIcon={<AttachFileIcon />}
            disabled={disabled}
            onClick={() => inputRef.current?.click()}
          >
            Choose File
          </Button>
          {file && <Chip icon={<AttachFileIcon />} label={file.name} variant="outlined" />}
        </Stack>
      </Stack>
      <input
        ref={inputRef}
        type="file"
        accept=".jsonl,application/json,text/plain"
        hidden
        onChange={handleInput}
      />
    </Paper>
  );
}

