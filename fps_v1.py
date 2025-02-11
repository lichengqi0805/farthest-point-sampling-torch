import numpy as np
import torch
    
class FPS:
    def __init__(self, pcd_xyz, n_samples):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.n_samples = n_samples
        self.pcd_xyz = pcd_xyz
        self.n_pts = pcd_xyz.shape[0]
        self.dim = pcd_xyz.shape[1]
        self.selected_pts = None
        self.selected_pts_expanded = torch.zeros(size=(n_samples, 1, self.dim)).to(self.device)
        self.remaining_pts = torch.from_numpy(pcd_xyz).double().to(self.device)

        self.grouping_radius = None
        self.dist_pts_to_selected = None  # Iteratively updated in step(). Finally re-used in group()
        self.labels = None

        # Random pick a start
        self.start_idx = np.random.randint(low=0, high=self.n_pts - 1)
        self.selected_pts_expanded[0] = self.remaining_pts[self.start_idx]
        self.n_selected_pts = 1

    def get_selected_pts(self):
        self.selected_pts = torch.squeeze(self.selected_pts_expanded, dim=1)
        return self.selected_pts.cpu()

    def step(self):
        if self.n_selected_pts < self.n_samples:
            self.dist_pts_to_selected = self.__distance__(self.remaining_pts, self.selected_pts_expanded[:self.n_selected_pts]).T
            dist_pts_to_selected_min, _ = torch.min(self.dist_pts_to_selected, dim=1, keepdim=True)
            res_selected_idx = torch.argmax(dist_pts_to_selected_min)
            self.selected_pts_expanded[self.n_selected_pts] = self.remaining_pts[res_selected_idx]

            self.n_selected_pts += 1
        else:
            print("Got enough number samples")


    def fit(self):
        for _ in range(1, self.n_samples):
            self.step()
        return self.get_selected_pts()

    def group(self, radius):
        self.grouping_radius = radius   # the grouping radius is not actually used
        dists = self.dist_pts_to_selected

        # Ignore the "points"-"selected" relations if it's larger than the radius
        dists = np.where(dists > radius, dists+1000000*radius, dists)

        # Find the relation with the smallest distance.
        # NOTE: the smallest distance may still larger than the radius.
        self.labels = np.argmin(dists, axis=1)
        return self.labels


    @staticmethod
    def __distance__(a, b):        
        return torch.norm(a - b, p=2, dim=2)