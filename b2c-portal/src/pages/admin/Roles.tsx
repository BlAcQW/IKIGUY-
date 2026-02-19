import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Shield,
  Plus,
  Edit,
  Trash2,
  Loader2,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

interface Permission {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[];
  userCount: number;
  isSystem: boolean;
}

export default function Roles() {
  const [roles, setRoles] = useState<Role[]>([
    {
      id: '1',
      name: 'Admin',
      description: 'Full system access',
      permissions: ['users.read', 'users.write', 'users.delete', 'system.read', 'system.write'],
      userCount: 3,
      isSystem: true,
    },
    {
      id: '2',
      name: 'User',
      description: 'Standard user access',
      permissions: ['voice.read', 'voice.write', 'automations.read', 'automations.write'],
      userCount: 15,
      isSystem: true,
    },
    {
      id: '3',
      name: 'Moderator',
      description: 'Moderate content and users',
      permissions: ['users.read', 'voice.read', 'voice.write', 'automations.read'],
      userCount: 5,
      isSystem: false,
    },
  ]);

  const [availablePermissions] = useState<Permission[]>([
    { id: 'users.read', name: 'Read Users', description: 'View user information', enabled: false },
    { id: 'users.write', name: 'Write Users', description: 'Create and edit users', enabled: false },
    { id: 'users.delete', name: 'Delete Users', description: 'Delete user accounts', enabled: false },
    { id: 'voice.read', name: 'Read Voice Agents', description: 'View voice agents', enabled: false },
    { id: 'voice.write', name: 'Write Voice Agents', description: 'Create and edit voice agents', enabled: false },
    { id: 'automations.read', name: 'Read Automations', description: 'View automations', enabled: false },
    { id: 'automations.write', name: 'Write Automations', description: 'Create and edit automations', enabled: false },
    { id: 'system.read', name: 'Read System', description: 'View system settings', enabled: false },
    { id: 'system.write', name: 'Write System', description: 'Modify system settings', enabled: false },
  ]);

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [newRole, setNewRole] = useState({
    name: '',
    description: '',
    permissions: [] as string[],
  });

  const handleCreateRole = () => {
    const role: Role = {
      id: Date.now().toString(),
      name: newRole.name,
      description: newRole.description,
      permissions: newRole.permissions,
      userCount: 0,
      isSystem: false,
    };

    setRoles([...roles, role]);
    setIsCreateDialogOpen(false);
    setNewRole({ name: '', description: '', permissions: [] });

    toast({
      title: 'Success',
      description: 'Role created successfully',
    });
  };

  const handleUpdateRole = () => {
    if (!editingRole) return;

    setRoles(roles.map(r => r.id === editingRole.id ? editingRole : r));
    setIsEditDialogOpen(false);
    setEditingRole(null);

    toast({
      title: 'Success',
      description: 'Role updated successfully',
    });
  };

  const handleDeleteRole = (roleId: string) => {
    const role = roles.find(r => r.id === roleId);

    if (role?.isSystem) {
      toast({
        title: 'Error',
        description: 'Cannot delete system roles',
        variant: 'destructive',
      });
      return;
    }

    if (!confirm('Are you sure you want to delete this role?')) return;

    setRoles(roles.filter(r => r.id !== roleId));

    toast({
      title: 'Success',
      description: 'Role deleted successfully',
    });
  };

  const togglePermission = (permissionId: string, role: any, isNew: boolean = false) => {
    if (isNew) {
      const hasPermission = newRole.permissions.includes(permissionId);
      setNewRole({
        ...newRole,
        permissions: hasPermission
          ? newRole.permissions.filter(p => p !== permissionId)
          : [...newRole.permissions, permissionId],
      });
    } else if (role) {
      const hasPermission = role.permissions.includes(permissionId);
      setEditingRole({
        ...role,
        permissions: hasPermission
          ? role.permissions.filter((p: string) => p !== permissionId)
          : [...role.permissions, permissionId],
      });
    }
  };

  return (
    <div className="p-8 pb-12">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Roles & Permissions</h1>
        <p className="text-muted-foreground">Manage user roles and access permissions</p>
      </div>

      {/* Create Role Button */}
      <div className="mb-6 flex justify-end">
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Role
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Role</DialogTitle>
              <DialogDescription>
                Define a new role with specific permissions
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="role-name">Role Name</Label>
                <Input
                  id="role-name"
                  value={newRole.name}
                  onChange={(e) => setNewRole({ ...newRole, name: e.target.value })}
                  placeholder="e.g., Content Manager"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="role-description">Description</Label>
                <Input
                  id="role-description"
                  value={newRole.description}
                  onChange={(e) => setNewRole({ ...newRole, description: e.target.value })}
                  placeholder="Describe this role's purpose"
                />
              </div>
              <div className="grid gap-2">
                <Label>Permissions</Label>
                <div className="border rounded-lg p-4 space-y-2 max-h-[300px] overflow-y-auto">
                  {availablePermissions.map((permission) => (
                    <div key={permission.id} className="flex items-center justify-between py-2 border-b last:border-0">
                      <div className="flex-1">
                        <div className="font-medium text-sm">{permission.name}</div>
                        <div className="text-xs text-muted-foreground">{permission.description}</div>
                      </div>
                      <Switch
                        checked={newRole.permissions.includes(permission.id)}
                        onCheckedChange={() => togglePermission(permission.id, null, true)}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateRole} disabled={!newRole.name}>
                Create Role
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Roles Table */}
      <Card>
        <CardHeader>
          <CardTitle>System Roles</CardTitle>
          <CardDescription>
            Total: {roles.length} roles
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Role</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Users</TableHead>
                <TableHead>Permissions</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {roles.map((role) => (
                <TableRow key={role.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-primary" />
                      <div>
                        <div className="font-medium">{role.name}</div>
                        {role.isSystem && (
                          <Badge variant="outline" className="mt-1">System Role</Badge>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm text-muted-foreground">{role.description}</div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary">{role.userCount} users</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {role.permissions.slice(0, 3).map((permission) => (
                        <Badge key={permission} variant="outline" className="text-xs">
                          {permission}
                        </Badge>
                      ))}
                      {role.permissions.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{role.permissions.length - 3} more
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => {
                          setEditingRole(role);
                          setIsEditDialogOpen(true);
                        }}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteRole(role.id)}
                        disabled={role.isSystem}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Edit Role Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Role</DialogTitle>
            <DialogDescription>
              Update role information and permissions
            </DialogDescription>
          </DialogHeader>
          {editingRole && (
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="edit-role-name">Role Name</Label>
                <Input
                  id="edit-role-name"
                  value={editingRole.name}
                  onChange={(e) => setEditingRole({ ...editingRole, name: e.target.value })}
                  disabled={editingRole.isSystem}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit-role-description">Description</Label>
                <Input
                  id="edit-role-description"
                  value={editingRole.description}
                  onChange={(e) => setEditingRole({ ...editingRole, description: e.target.value })}
                />
              </div>
              <div className="grid gap-2">
                <Label>Permissions</Label>
                <div className="border rounded-lg p-4 space-y-2 max-h-[300px] overflow-y-auto">
                  {availablePermissions.map((permission) => (
                    <div key={permission.id} className="flex items-center justify-between py-2 border-b last:border-0">
                      <div className="flex-1">
                        <div className="font-medium text-sm">{permission.name}</div>
                        <div className="text-xs text-muted-foreground">{permission.description}</div>
                      </div>
                      <Switch
                        checked={editingRole.permissions.includes(permission.id)}
                        onCheckedChange={() => togglePermission(permission.id, editingRole, false)}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateRole}>
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
