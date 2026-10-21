import Typography from "@mui/material/Typography";

export default function PlaceholderPage({ title }: { title: string }) {
  return (
    <Typography variant="h4" component="h1">
      {title}
    </Typography>
  );
}
